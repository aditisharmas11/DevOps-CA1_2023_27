const LoadingSpinner = () => {
  return (
    <div className="flex flex-col items-center gap-4 py-10 animate-fade-in">
      <div className="relative h-14 w-14">
        <div className="absolute inset-0 rounded-full border border-border" />
        <div className="absolute inset-0 rounded-full border border-transparent border-t-primary animate-spin-slow" />
      </div>
      <p className="text-sm text-muted-foreground">Running detection and Grad-CAM…</p>
    </div>
  );
};

export default LoadingSpinner;
