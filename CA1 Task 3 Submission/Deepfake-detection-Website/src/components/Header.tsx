import { Shield } from "lucide-react";

const Header = () => {
  return (
    <header className="w-full py-6 px-4 text-center">
      <div className="flex items-center justify-center gap-3">
        <Shield className="w-8 h-8 text-primary animate-pulse-glow" />
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
          Deepfake <span className="text-primary text-glow-primary">Detector</span>
        </h1>
      </div>
      <p className="mt-2 text-muted-foreground text-sm">
        Upload an image to analyze its authenticity using AI
      </p>
    </header>
  );
};

export default Header;
