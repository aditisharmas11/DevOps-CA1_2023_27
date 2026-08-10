import { useCallback, useState } from "react";
import { Upload, X } from "lucide-react";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  preview: string | null;
  onClear: () => void;
}

const UploadZone = ({ onFileSelect, preview, onClear }: UploadZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    if (!file.type.includes("jpeg") && !file.type.includes("jpg")) {
      setError("Only JPEG images are accepted");
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File must be under 10MB");
      return false;
    }
    setError(null);
    return true;
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && validateFile(file)) onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) onFileSelect(file);
  };

  if (preview) {
    return (
      <div className="relative overflow-hidden rounded-lg border border-border bg-secondary/40 animate-fade-in">
        <img
          src={preview}
          alt="Uploaded preview"
          className="w-full max-h-80 object-contain"
        />
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent animate-scan-line" />
        </div>
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear image"
          className="absolute top-3 right-3 rounded-md border border-border bg-background/90 p-1.5 text-foreground transition-colors hover:border-destructive hover:text-destructive"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border border-dashed px-8 py-14 transition-colors duration-300 ${
          isDragging
            ? "border-primary bg-primary/10"
            : "border-border hover:border-primary/50 hover:bg-secondary/50"
        }`}
      >
        <div
          className={`rounded-full p-3 transition-colors ${
            isDragging ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"
          }`}
        >
          <Upload className="h-7 w-7" strokeWidth={1.5} />
        </div>
        <div className="text-center">
          <p className="font-medium text-foreground">
            {isDragging ? "Drop image to analyze" : "Drop a JPEG here"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">or click to browse · max 10MB</p>
        </div>
        <input
          type="file"
          accept="image/jpeg,image/jpg"
          onChange={handleChange}
          className="hidden"
        />
      </label>
      {error && (
        <p className="mt-3 text-center text-sm text-destructive animate-fade-in">{error}</p>
      )}
    </div>
  );
};

export default UploadZone;
