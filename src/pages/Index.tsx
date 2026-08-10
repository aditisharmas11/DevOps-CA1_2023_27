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
  heatmap_base64: string | null;
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

      if (!response.ok) {
        let detail = `Server error: ${response.status}`;
        try {
          const errBody = await response.json();
          if (errBody?.detail) detail = String(errBody.detail);
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }

      const data: PredictionResult = await response.json();
      setResult(data);
    } catch (err) {
      toast({
        title: "Analysis failed",
        description:
          err instanceof Error
            ? err.message
            : "Could not reach the detection server. Is the backend running?",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            "linear-gradient(hsl(var(--foreground)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      <div className="relative z-10 flex min-h-screen flex-col items-center px-4 pb-12">
        <Header />

        <main className="mt-2 w-full max-w-lg space-y-5">
          <section className="panel rounded-lg p-5 sm:p-6">
            <UploadZone
              onFileSelect={handleFileSelect}
              preview={preview}
              onClear={handleClear}
            />
          </section>

          {file && !loading && (
            <div className="animate-fade-in">
              <Button onClick={handleDetect} size="lg" className="w-full gap-2">
                <ScanSearch className="h-5 w-5" />
                Detect deepfake
              </Button>
            </div>
          )}

          {loading && <LoadingSpinner />}

          {result && !loading && (
            <ResultCard
              fakeProbability={result.fake_probability}
              isFake={result.is_fake}
              heatmapBase64={result.heatmap_base64}
              preview={preview}
            />
          )}
        </main>

        <footer className="mt-auto pt-10 text-center text-xs text-muted-foreground">
          Deep Eye Vision · Research use only · Not a forensic verdict
        </footer>
      </div>
    </div>
  );
};

export default Index;
