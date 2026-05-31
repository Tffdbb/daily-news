// Go Crypto 采集器 v5
// 功能：多交易所行情采集 + 备选API补全 + 指数退避重试 + 原子写入 + R24三态报告
// v5: ①指数退避重试(2s/4s/8s带抖动, DNS/网络不可达快速失败)
//      ②single mode串行请求精确保守限速(PRISM 5/min)
//      ③跨交易所备选补全(失败了后续API自动补)

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// ========== 数据模型 ==========
type Ticker struct {
	Symbol string  `json:"symbol"`
	Price  float64 `json:"price"`
	Change float64 `json:"change"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Vol    float64 `json:"volume"`
	Source string  `json:"source"`
}

type Report struct {
	Success int      `json:"success"`
	Fail    int      `json:"fail"`
	Unknown int      `json:"unknown"`
	Errors  []ErrLog `json:"errors"`
}

type ErrLog struct {
	Source  string `json:"source"`
	Reason  string `json:"reason"`
	Unknown bool   `json:"unknown,omitempty"`
}

type Result struct {
	CollectedAt string   `json:"collectedAt"`
	Tickers     []Ticker `json:"tickers"`
	Report      Report   `json:"report"`
	Duration    string   `json:"duration"`
}

// API配置
type apiConfig struct {
	name            string
	mode            string // "batch" or "single"
	url             string // batch=完整URL, single=含%s模板
	parse           func(body []byte) ([]Ticker, error)
	rateLimitPerMin int // 0=无限制
}

var report = Report{}
var coins = []string{"BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "DOT", "AVAX", "LINK", "POL", "AAVE", "UNI", "ARB", "OP", "ATOM", "NEAR"}

var apis = []apiConfig{
	{
		name: "binance",
		mode: "batch",
		url:  "https://api.binance.com/api/v3/ticker/24hr?symbols=%5B%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22,%22XRPUSDT%22,%22DOGEUSDT%22,%22ADAUSDT%22,%22DOTUSDT%22,%22AVAXUSDT%22,%22LINKUSDT%22,%22POLUSDT%22,%22AAVEUSDT%22,%22UNIUSDT%22,%22ARBUSDT%22,%22OPUSDT%22,%22ATOMUSDT%22,%22NEARUSDT%22%5D",
		parse: parseBinance,
	},
	{
		name: "coincap",
		mode: "batch",
		url:  "https://api.coincap.io/v2/assets?ids=bitcoin,ethereum,solana,xrp,dogecoin,cardano,polkadot,avalanche,chainlink,polygon,aave,uniswap,arbitrum,optimism,cosmos,near&limit=16",
		parse: parseCoinCap,
	},
	{
		name: "okx",
		mode: "batch",
		url:  "https://www.okx.com/api/v5/market/tickers?instType=SPOT",
		parse: parseOKX,
	},
	{
		name: "bybit",
		mode: "batch",
		url:  "https://api.bybit.com/v5/market/tickers?category=spot",
		parse: parseBybit,
	},
	{
		name: "kucoin",
		mode: "batch",
		url:  "https://api.kucoin.com/api/v1/market/allTickers",
		parse: parseKuCoin,
	},
	{
		name:            "prism",
		mode:            "single",
		url:             "https://api.prismapi.ai/crypto/price/%s?currency=USD",
		parse:           parsePrism,
		rateLimitPerMin: 5,
	},
}

// ========== PRISM 解析 ==========
type prismResp struct {
	Symbol    string  `json:"symbol"`
	PriceUSD  float64 `json:"price_usd"`
	Change24h float64 `json:"change_24h_pct"`
	Volume24h float64 `json:"volume_24h"`
}

func parsePrism(body []byte) ([]Ticker, error) {
	var raw prismResp
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse prism: %w", err)
	}
	return []Ticker{{
		Symbol: raw.Symbol,
		Price:  raw.PriceUSD,
		Change: raw.Change24h,
		Vol:    raw.Volume24h,
		Source: "prism",
	}}, nil
}

// ========== Binance 解析 ==========
type binanceTicker struct {
	Symbol      string `json:"symbol"`
	LastPrice   string `json:"lastPrice"`
	PriceChange string `json:"priceChangePercent"`
	HighPrice   string `json:"highPrice"`
	LowPrice    string `json:"lowPrice"`
	Volume      string `json:"quoteVolume"`
}

func parseBinance(body []byte) ([]Ticker, error) {
	var raw []binanceTicker
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse binance: %w", err)
	}
	var result []Ticker
	for _, t := range raw {
		sym := strings.TrimSuffix(t.Symbol, "USDT")
		result = append(result, Ticker{
			Symbol: sym,
			Price:  parseFloat(t.LastPrice),
			Change: parseFloat(t.PriceChange),
			High:   parseFloat(t.HighPrice),
			Low:    parseFloat(t.LowPrice),
			Vol:    parseFloat(t.Volume),
			Source: "binance",
		})
	}
	return result, nil
}

// ========== CoinCap 解析 ==========
type coincapData struct {
	Data []coincapAsset `json:"data"`
}
type coincapAsset struct {
	Symbol    string `json:"symbol"`
	PriceUSD  string `json:"priceUsd"`
	Change24h string `json:"changePercent24Hr"`
	Volume24h string `json:"volumeUsd24Hr"`
}

func parseCoinCap(body []byte) ([]Ticker, error) {
	var raw coincapData
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse coincap: %w", err)
	}
	var result []Ticker
	for _, a := range raw.Data {
		result = append(result, Ticker{
			Symbol: strings.ToUpper(a.Symbol),
			Price:  parseFloat(a.PriceUSD),
			Change: parseFloat(a.Change24h),
			Vol:    parseFloat(a.Volume24h),
			Source: "coincap",
		})
	}
	return result, nil
}

// ========== OKX 解析 ==========
type okxTicker struct {
	InstID  string `json:"instId"`
	Last    string `json:"last"`
	Vol24h  string `json:"volCcy24h"`
	High24h string `json:"high24h"`
	Low24h  string `json:"low24h"`
}

func parseOKX(body []byte) ([]Ticker, error) {
	var raw struct {
		Code string      `json:"code"`
		Data []okxTicker `json:"data"`
	}
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse okx: %w", err)
	}
	if raw.Code != "0" {
		return nil, fmt.Errorf("okx error code: %s", raw.Code)
	}
	coinMap := make(map[string]bool)
	for _, c := range coins {
		coinMap[c] = true
	}
	var result []Ticker
	for _, t := range raw.Data {
		sym := strings.TrimSuffix(t.InstID, "-USDT")
		if !coinMap[sym] {
			continue
		}
		result = append(result, Ticker{
			Symbol: sym,
			Price:  parseFloat(t.Last),
			High:   parseFloat(t.High24h),
			Low:    parseFloat(t.Low24h),
			Vol:    parseFloat(t.Vol24h),
			Source: "okx",
		})
	}
	return result, nil
}

// ========== Bybit 解析 ==========
type bybitResp struct {
	Result bybitResult `json:"result"`
}
type bybitResult struct {
	List []bybitTicker `json:"list"`
}
type bybitTicker struct {
	Symbol      string `json:"symbol"`
	LastPrice   string `json:"lastPrice"`
	Price24hPct string `json:"price24hPcnt"`
	High24h     string `json:"highPrice24h"`
	Low24h      string `json:"lowPrice24h"`
	Volume24h   string `json:"volume24h"`
}

func parseBybit(body []byte) ([]Ticker, error) {
	var raw bybitResp
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse bybit: %w", err)
	}
	coinMap := make(map[string]bool)
	for _, c := range coins {
		coinMap[c] = true
	}
	var result []Ticker
	for _, t := range raw.Result.List {
		sym := strings.TrimSuffix(t.Symbol, "USDT")
		if !coinMap[sym] {
			continue
		}
		result = append(result, Ticker{
			Symbol: sym,
			Price:  parseFloat(t.LastPrice),
			Change: parseFloat(t.Price24hPct),
			High:   parseFloat(t.High24h),
			Low:    parseFloat(t.Low24h),
			Vol:    parseFloat(t.Volume24h),
			Source: "bybit",
		})
	}
	return result, nil
}

// ========== KuCoin 解析 ==========
type kucoinResp struct {
	Data kucoinData `json:"data"`
}
type kucoinData struct {
	Ticker []kucoinTicker `json:"ticker"`
}
type kucoinTicker struct {
	Symbol     string `json:"symbol"`
	Last       string `json:"last"`
	ChangeRate string `json:"changeRate"`
	High       string `json:"high"`
	Low        string `json:"low"`
	VolValue   string `json:"volValue"`
}

func parseKuCoin(body []byte) ([]Ticker, error) {
	var raw kucoinResp
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("parse kucoin: %w", err)
	}
	coinMap := make(map[string]bool)
	for _, c := range coins {
		coinMap[c] = true
	}
	var result []Ticker
	for _, t := range raw.Data.Ticker {
		parts := strings.SplitN(t.Symbol, "-", 2)
		if len(parts) < 2 {
			continue
		}
		sym := parts[0]
		if sym != strings.ToUpper(sym) {
			continue
		}
		if !coinMap[sym] {
			continue
		}
		changePct := parseFloat(t.ChangeRate) * 100
		result = append(result, Ticker{
			Symbol: sym,
			Price:  parseFloat(t.Last),
			Change: changePct,
			High:   parseFloat(t.High),
			Low:    parseFloat(t.Low),
			Vol:    parseFloat(t.VolValue),
			Source: "kucoin",
		})
	}
	return result, nil
}

// ========== 工具函数 ==========
func parseFloat(s string) float64 {
	var v float64
	fmt.Sscanf(s, "%f", &v)
	return v
}

// isFastFail 判断是否DNS/网络不可达（不重试）
func isFastFail(err error) bool {
	if err == nil {
		return false
	}
	msg := err.Error()
	return strings.Contains(msg, "no such host") ||
		strings.Contains(msg, "getaddrinfow") ||
		strings.Contains(msg, "no data") ||
		strings.Contains(msg, "connection refused") ||
		strings.Contains(msg, "no route to host") ||
		strings.Contains(msg, "network is unreachable")
}

// atomicWrite: 先写.tmp再rename，保证写入不损坏现有文件
func atomicWrite(filePath string, data []byte) error {
	dir := filepath.Dir(filePath)
	base := filepath.Base(filePath)
	tmp := filepath.Join(dir, fmt.Sprintf(".%s.tmp.%d", base, rand.Int63()))
	if err := os.WriteFile(tmp, data, 0644); err != nil {
		return err
	}
	return os.Rename(tmp, filePath)
}

// ========== R24三态报告 ==========
func (r *Report) logError(source, reason string) {
	r.Fail++
	r.Errors = append(r.Errors, ErrLog{Source: source, Reason: reason})
}

func (r *Report) logSuccess() {
	r.Success++
}

func (r *Report) logUnknown(source, reason string) {
	r.Unknown++
	r.Errors = append(r.Errors, ErrLog{Source: source, Reason: reason, Unknown: true})
}

// ========== 指数退避重试HTTP请求 ==========
// 退避: 2s, 4s, 8s（带±25%随机抖动）
// DNS/网络不可达: 快速失败，不重试
// HTTP 4xx/5xx: 重试（429限流也重试）
// apiHTTP 封装带指数退避重试
// 超时5s，2次重试（1s/2s），超时/限流也快速切不等待
func apiHTTP(url string) ([]byte, error) {
	backoffs := []time.Duration{1 * time.Second, 2 * time.Second}
	var lastErr error

	for attempt := 0; attempt <= len(backoffs); attempt++ {
		client := &http.Client{Timeout: 5 * time.Second}
		resp, err := client.Get(url)
		if err == nil {
			body, readErr := io.ReadAll(resp.Body)
			resp.Body.Close()
			if readErr != nil {
				lastErr = readErr
				continue
			}
			if resp.StatusCode == 429 {
				return nil, fmt.Errorf("rate limited (429), switching")
			}
			if resp.StatusCode >= 400 {
				lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
				continue
			}
			return body, nil
		}
		lastErr = err

		// DNS/网络不可达 → 快速失败，不重试
		if isFastFail(lastErr) {
			return nil, fmt.Errorf("fast fail: %w", lastErr)
		}

		// 超时 → 快速切换，不重试（超时后重试大概率也超时）
		if strings.Contains(lastErr.Error(), "context deadline exceeded") ||
			strings.Contains(lastErr.Error(), "Client.Timeout") {
			return nil, fmt.Errorf("timeout, switching: %w", lastErr)
		}

		// 最后一次尝试失败（不重试了）
		if attempt == len(backoffs) {
			return nil, fmt.Errorf("all retries exhausted: %w", lastErr)
		}

		// 指数退避 + 随机抖动
		sleep := backoffs[attempt]
		jitter := time.Duration(float64(sleep) * 0.25 * (2*rand.Float64() - 1))
		sleep += jitter
		fmt.Fprintf(os.Stderr, "    [retry %d/%d] wait %v after: %v\n",
			attempt+1, len(backoffs), sleep.Round(time.Millisecond), lastErr)
		time.Sleep(sleep)
	}
	return nil, fmt.Errorf("unreachable")}

// ========== 限速器（串行安全）==========
type rateLimiter struct {
	interval time.Duration
	last     time.Time
	mu       sync.Mutex
}

func newRateLimiter(reqPerMin int) *rateLimiter {
	if reqPerMin <= 0 {
		return nil
	}
	return &rateLimiter{
		interval: time.Duration(60.0/float64(reqPerMin)*1000) * time.Millisecond,
	}
}

// wait 保证相邻两次返回之间的间隔 >= interval
// 即使被多个goroutine并发调用也安全（串行化在mutex内）
func (rl *rateLimiter) wait() {
	if rl == nil {
		return
	}
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	if rl.last.IsZero() {
		rl.last = now
		return
	}
	elapsed := now.Sub(rl.last)
	if elapsed < rl.interval {
		sleep := rl.interval - elapsed
		time.Sleep(sleep)
		rl.last = time.Now()
	} else {
		rl.last = now
	}
}

// ========== 获取缺失币种列表 ==========
func getMissing(seen map[string]bool) []string {
	var missing []string
	for _, c := range coins {
		if !seen[c] {
			missing = append(missing, c)
		}
	}
	return missing
}

// ========== API请求结果通道 ==========
type apiResult struct {
	name    string
	tickers []Ticker
	err     error
}

// fetchBatch 并发请求一个batch API
func fetchBatch(api apiConfig, ch chan<- apiResult) {
	body, err := apiHTTP(api.url)
	if err != nil {
		ch <- apiResult{name: api.name, err: err}
		return
	}
	tickers, err := api.parse(body)
	if err != nil {
		ch <- apiResult{name: api.name, err: fmt.Errorf("parse: %w", err)}
		return
	}
	ch <- apiResult{name: api.name, tickers: tickers}
}

// ========== 主逻辑 ==========
func main() {
	start := time.Now()

	// 日志全部输出到 stderr，stdout 只输出 JSON
	log := func(format string, args ...interface{}) {
		fmt.Fprintf(os.Stderr, format+"\n", args...)
	}

	log("=== Go Crypto Collector v5 ===")

	allTickers := []Ticker{}
	seen := make(map[string]bool)
	var mu sync.Mutex // 保护 seen/allTickers

	// ===== 第一阶段：所有 batch API 并行 =====
	log("▶ Phase 1: 并行请求 %d 个batch API...", len(apis)-1)
	ch := make(chan apiResult, len(apis))
	for _, api := range apis {
		if api.mode == "batch" {
			go fetchBatch(api, ch)
		}
	}

	// 收集 batch 结果
	batchCount := 0
	for i := 0; i < len(apis)-1; i++ {
		r := <-ch
		if r.err != nil {
			report.logError(r.name+"_fetch", r.err.Error())
			log("    %s: ❌ %v", r.name, r.err)
			continue
		}
		mu.Lock()
		newCount := 0
		for _, t := range r.tickers {
			if !seen[t.Symbol] {
				allTickers = append(allTickers, t)
				seen[t.Symbol] = true
				newCount++
			}
		}
		mu.Unlock()
		batchCount++
		if newCount > 0 {
			report.logSuccess()
			log("    %s: +%d 新币 (累计 %d/%d)", r.name, newCount, len(seen), len(coins))
		} else {
			report.logError(r.name+"_stale", "no new symbols")
			log("    %s: 0 新币 (已有全部 %d 币)", r.name, len(seen))
		}
	}

	log("▶ Phase 1 完成: %d/%d API成功, 已获 %d/%d 币",
		batchCount, len(apis)-1, len(seen), len(coins))

	// ===== 第二阶段：single mode 补漏 (PRISM) =====
	for _, api := range apis {
		if api.mode != "single" {
			continue
		}
		mu.Lock()
		missing := getMissing(seen)
		mu.Unlock()

		if len(missing) == 0 {
			log("▶ Phase 2: %s 跳过（已全部获取）", api.name)
			break
		}

		log("▶ Phase 2: %s 补漏 %d 币 (限速 %d/min)...",
			api.name, len(missing), api.rateLimitPerMin)
		rl := newRateLimiter(api.rateLimitPerMin)
		newCount := 0

		for _, symbol := range missing {
			rl.wait()

			url := fmt.Sprintf(api.url, symbol)
			body, err := apiHTTP(url)
			if err != nil {
				report.logError(api.name+"_"+symbol, err.Error())
				log("      %s/%s: ❌ %v", api.name, symbol, err)
				continue
			}
			tickers, err := api.parse(body)
			if err != nil {
				report.logError(api.name+"_parse_"+symbol, err.Error())
				log("      %s/%s: ❌ parse: %v", api.name, symbol, err)
				continue
			}
			mu.Lock()
			for _, t := range tickers {
				if !seen[t.Symbol] {
					allTickers = append(allTickers, t)
					seen[t.Symbol] = true
					newCount++
				}
			}
			mu.Unlock()
			log("      %s/%s: ✅ (累计 %d/%d)", api.name, symbol, len(seen), len(coins))
		}

		if newCount > 0 {
			report.logSuccess()
		} else if len(missing) > 0 {
			report.logError(api.name+"_empty",
				fmt.Sprintf("got 0 of %d missing", len(missing)))
		}
		log("    %s: +%d 新币 (累计 %d/%d)", api.name, newCount, len(seen), len(coins))
	}

	// R24: 标记最终缺失的币
	for _, c := range coins {
		if !seen[c] {
			report.logUnknown("missing", c)
		}
	}

	// 原子写入
	result := Result{
		CollectedAt: time.Now().UTC().Format(time.RFC3339),
		Tickers:     allTickers,
		Report:      report,
		Duration:    time.Since(start).Round(time.Millisecond).String(),
	}
	data, _ := json.MarshalIndent(result, "", "  ")

	// stdout 只输出 JSON（Actions 友好：管道接收的就是 JSON）
	fmt.Println(string(data))

	outputPath := filepath.Join(".", "crypto_result.json")
	if err := atomicWrite(outputPath, data); err != nil {
		log("  ❌ Write failed: %v", err)
		report.logError("write", err.Error())
		// 兜底：直接写
		if e2 := os.WriteFile(outputPath, data, 0644); e2 != nil {
			log("  ❌ Fallback write also failed: %v", e2)
		}
	} else {
		log("  💾 Written: %s (%d bytes)", outputPath, len(data))
	}

	// 三态报告（stderr）
	log("")
	log("  📊 报告: %d 成功 | %d 失败 | %d 未知",
		report.Success, report.Fail, report.Unknown)
	log("  📈 币种: %d/%d | 价格点数: %d",
		len(seen), len(coins), len(allTickers))
	if len(report.Errors) > 0 {
		log("  --- 错误详情 ---")
		for _, e := range report.Errors {
			tag := "❌"
			if e.Unknown {
				tag = "❓"
			}
			log("  %s %s: %s", tag, e.Source, e.Reason)
		}
	}

	log("")
	log("  ⏱ 耗时: %s", time.Since(start).Round(time.Millisecond))
	log("  ✅ Done")
}
