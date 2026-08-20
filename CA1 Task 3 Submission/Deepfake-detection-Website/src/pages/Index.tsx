import { useState } from "react";
import { ScanSearch } from "lucide-react";
import Header from "@/components/Header";
import UploadZone from "@/components/UploadZone";
import ResultCard from "@/components/ResultCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface PredictionResult {
  fake_probability: number;
  is_fake: boolean;
}

const Index = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const { toast } = useToast();

  const handleFileSelect = (selected: File) => {
    setFile(selected);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(selected);
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  const handleDetect = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/predict", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data: PredictionResult = await response.json();
      setResult(data);
    } catch (err) {
      toast({
        title: "Analysis Failed",
        description: err instanceof Error ? err.message : "Could not reach the detection server. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background grid effect */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--primary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />
      {/* Radial glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] opacity-20 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse, hsl(190 100% 50% / 0.3), transparent 70%)",
        }}
      />

      <div className="relative z-10 flex flex-col items-center min-h-screen px-4 pb-12">
        <Header />

        <main className="w-full max-w-lg space-y-6 mt-4">
          {/* Upload Card */}
          <div className="glass rounded-xl p-6">
            <UploadZone onFileSelect={handleFileSelect} preview={preview} onClear={handleClear} />
          </div>

          {/* Action Button */}
          {file && !loading && (
            <div className="animate-fade-in">
              <Button onClick={handleDetect} size="lg" className="w-full gap-2">
                <ScanSearch className="w-5 h-5" />
                Detect Fake
              </Button>
            </div>
          )}

          {/* Loading */}
          {loading && <LoadingSpinner />}

          {/* Results */}
          {result && !loading && (
            <ResultCard fakeProbability={result.fake_probability} isFake={result.is_fake} />
          )}
        </main>

        <footer className="mt-auto pt-8 text-center text-xs text-muted-foreground">
          Deepfake Detector · For research purposes only
        </footer>
      </div>
    </div>
  );
};

export default Index;
