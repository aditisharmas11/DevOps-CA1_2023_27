import { useEffect, useState } from "react";
import { ShieldAlert, ShieldCheck } from "lucide-react";

interface ResultCardProps {
  fakeProbability: number;
  isFake: boolean;
  heatmapBase64: string | null;
  preview: string | null;
}

const ResultCard = ({
  fakeProbability,
  isFake,
  heatmapBase64,
  preview,
}: ResultCardProps) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const percentage = Math.round(fakeProbability * 1000) / 10;

  useEffect(() => {
    let start = 0;
    const end = percentage;
    const duration = 1000;
    const stepTime = 16;
    const steps = duration / stepTime;
    const increment = end / steps;

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setAnimatedValue(end);
        clearInterval(timer);
      } else {
        setAnimatedValue(Math.round(start * 10) / 10);
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [percentage]);

  useEffect(() => {
    setShowHeatmap(Boolean(heatmapBase64));
  }, [heatmapBase64]);

  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (animatedValue / 100) * circumference;
  const heatmapSrc = heatmapBase64 ? `data:image/png;base64,${heatmapBase64}` : null;
  const displaySrc = showHeatmap && heatmapSrc ? heatmapSrc : preview;

  return (
    <div className="panel animate-fade-in space-y-6 rounded-lg p-6">
      <div className="flex flex-col items-center gap-4">
        <div className="relative h-32 w-32">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="hsl(var(--secondary))"
              strokeWidth="7"
            />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke={isFake ? "hsl(var(--destructive))" : "hsl(var(--success))"}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={`font-mono text-2xl font-semibold ${
                isFake ? "text-destructive" : "text-success"
              }`}
            >
              {animatedValue}%
            </span>
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
              fake score
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isFake ? (
            <ShieldAlert className="h-5 w-5 text-destructive" />
          ) : (
            <ShieldCheck className="h-5 w-5 text-success" />
          )}
          <span
            className={`text-lg font-semibold tracking-wide ${
              isFake ? "text-destructive" : "text-success"
            }`}
          >
            {isFake ? "Likely deepfake" : "Likely authentic"}
          </span>
        </div>
      </div>

      {displaySrc && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">
              {heatmapSrc
                ? "Model attention map (Grad-CAM)"
                : "Result preview"}
            </p>
            {heatmapSrc && preview && (
              <div className="flex rounded-md border border-border p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setShowHeatmap(false)}
                  className={`rounded px-2.5 py-1 transition-colors ${
                    !showHeatmap
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Original
                </button>
                <button
                  type="button"
                  onClick={() => setShowHeatmap(true)}
                  className={`rounded px-2.5 py-1 transition-colors ${
                    showHeatmap
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Heatmap
                </button>
              </div>
            )}
          </div>
          <div className="overflow-hidden rounded-md border border-border bg-secondary/30">
            <img
              src={displaySrc}
              alt={showHeatmap ? "Grad-CAM heatmap overlay" : "Original upload"}
              className="max-h-80 w-full object-contain animate-fade-in"
            />
          </div>
          {heatmapSrc && (
            <p className="text-xs leading-relaxed text-muted-foreground">
              Warmer regions are where the network focused when judging authenticity.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ResultCard;
