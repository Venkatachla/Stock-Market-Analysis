import re

with open('frontend/src/pages/StockDetail.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
    r'<div className="space-y-4">\s*<div className="bg-card border border-border/50 rounded-xl p-5 shadow-sm">\s*<h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2 mb-4">.*?<Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />',
    re.DOTALL
)

replacement = '''<div className="space-y-4">
            <div className="bg-card border border-border/50 rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-muted-foreground flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4" /> Professional Trade Signal
              </h3>
              {predData ? (
                <div className="space-y-4 text-sm font-medium">
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">1. Trend:</span>
                    <span>{predData.prob_up > 0.55 ? "Bullish" : predData.prob_down > 0.55 ? "Bearish" : "Sideways"}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">2. Signal:</span>
                    <span className={predData.confidence_score < 60 ? "text-yellow-500 font-bold" : (predData.prob_up > 0.55 ? "text-green-500 font-bold" : (predData.prob_down > 0.55 ? "text-red-500 font-bold" : "text-yellow-500 font-bold"))}>
                      {predData.confidence_score < 60 ? "WAIT" : (predData.prob_up > 0.55 ? "BUY" : (predData.prob_down > 0.55 ? "SELL" : "HOLD"))}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">3. Entry Zone:</span>
                    <span className="font-mono">₹{(predData.latest_price * 0.998).toFixed(1)} – ₹{(predData.latest_price * 1.002).toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">4. Stop Loss:</span>
                    <span className="font-mono text-red-400">₹{predData.stop_loss.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">5. Target:</span>
                    <span className="font-mono text-green-400">₹{predData.take_profit.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">6. Confidence:</span>
                    <span>{predData.confidence_score.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">7. Timeframe:</span>
                    <span>15 min</span>
                  </div>
                  <div className="flex justify-between items-center pb-2 border-b border-border/40">
                    <span className="text-muted-foreground">8. News Sentiment:</span>
                    <span>{predData.sentiment_score > 0.2 ? "Positive" : predData.sentiment_score < -0.2 ? "Negative" : "Neutral"}</span>
                  </div>
                  <div className="flex justify-between items-start pt-2">
                    <span className="text-muted-foreground mt-0.5 shrink-0 mr-4">9. Reason:</span>
                    <span className="text-right text-muted-foreground leading-tight">
                      {predData.prob_up > 0.55 
                        ? "Uptrend with positive AI orderflow." 
                        : predData.prob_down > 0.55 
                        ? "Downtrend with bearish distribution."
                        : "Consolidating price action without clear momentum."}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-sm flex-col gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                  <span className="text-muted-foreground">Generating Signal...</span>
                </div>
              )}
            </div>

            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 flex gap-3 items-start">
              <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />'''

new_content = pattern.sub(replacement, content)
with open('frontend/src/pages/StockDetail.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
