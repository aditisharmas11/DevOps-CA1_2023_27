import { useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert } from "lucide-react";

interface ResultCardProps {
  fakeProbability: number;
  isFake: boolean;
}

const ResultCard = ({ fakeProbability, isFake }: ResultCardProps) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const percentage = Math.round(fakeProbability * 1000) / 10;

  useEffect(() => {
    let start = 0;
    const end = percentage;
    const duration = 1200;
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

  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (animatedValue / 100) * circumference;

  return (
    <div
      className={`glass rounded-xl p-6 animate-fade-in ${
        isFake ? "glow-danger" : "glow-success"
      }`}
    >
      <div className="flex flex-col items-center gap-5">
        {/* Circular gauge */}
        <div className="relative w-36 h-36">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke="hsl(var(--secondary))"
              strokeWidth="8"
            />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              stroke={isFake ? "hsl(var(--destructive))" : "hsl(var(--success))"}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-1000 ease-out"
              style={{
                filter: isFake
                  ? "drop-shadow(0 0 6px hsl(0 72% 55% / 0.6))"
                  : "drop-shadow(0 0 6px hsl(145 65% 48% / 0.6))",
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className={`text-2xl font-bold font-mono ${
                isFake ? "text-destructive text-glow-danger" : "text-success text-glow-success"
              }`}
            >
              {animatedValue}%
            </span>
            <span className="text-xs text-muted-foreground">fake probability</span>
          </div>
        </div>

        {/* Label */}
        <div className="flex items-center gap-2">
          {isFake ? (
            <ShieldAlert className="w-6 h-6 text-destructive" />
          ) : (
            <ShieldCheck className="w-6 h-6 text-success" />
          )}
          <span
            className={`text-xl font-bold ${
              isFake ? "text-destructive text-glow-danger" : "text-success text-glow-success"
            }`}
          >
            {isFake ? "FAKE DETECTED" : "REAL IMAGE"}
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full">
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${
                isFake ? "bg-destructive" : "bg-success"
              }`}
              style={{
                width: `${animatedValue}%`,
                boxShadow: isFake
                  ? "0 0 10px hsl(0 72% 55% / 0.5)"
                  : "0 0 10px hsl(145 65% 48% / 0.5)",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultCard;
