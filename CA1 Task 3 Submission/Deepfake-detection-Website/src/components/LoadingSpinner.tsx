const LoadingSpinner = () => {
  return (
    <div className="flex flex-col items-center gap-4 py-8 animate-fade-in">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-secondary" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin-slow" 
          style={{ filter: "drop-shadow(0 0 8px hsl(190 100% 50% / 0.5))" }}
        />
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-b-primary/50 animate-spin-slow" 
          style={{ animationDirection: "reverse", animationDuration: "2s" }}
        />
      </div>
      <p className="text-sm text-muted-foreground animate-pulse-glow">
        Analyzing image authenticity...
      </p>
    </div>
  );
};

export default LoadingSpinner;
