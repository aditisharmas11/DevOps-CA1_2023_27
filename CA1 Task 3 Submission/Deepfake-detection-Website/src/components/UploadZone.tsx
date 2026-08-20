import { useCallback, useState } from "react";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";

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
      <div className="relative rounded-xl overflow-hidden glass animate-fade-in">
        <img
          src={preview}
          alt="Uploaded preview"
          className="w-full max-h-80 object-contain bg-background/50"
        />
        {/* Scan line effect */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent animate-scan-line" />
        </div>
        <button
          onClick={onClear}
          className="absolute top-3 right-3 p-1.5 rounded-full bg-background/80 text-foreground hover:bg-destructive hover:text-destructive-foreground transition-colors"
        >
          <X className="w-4 h-4" />
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
        className={`
          flex flex-col items-center justify-center gap-4 p-10 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-300
          ${
            isDragging
              ? "border-primary bg-primary/5 glow-primary"
              : "border-border hover:border-primary/50 hover:bg-primary/5"
          }
        `}
      >
        <div
          className={`p-4 rounded-full transition-colors duration-300 ${
            isDragging ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"
          }`}
        >
          {isDragging ? <ImageIcon className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
        </div>
        <div className="text-center">
          <p className="text-foreground font-medium">
            {isDragging ? "Drop your image here" : "Drag & drop a JPEG image"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">or click to browse</p>
        </div>
        <input
          type="file"
          accept="image/jpeg,image/jpg"
          onChange={handleChange}
          className="hidden"
        />
      </label>
      {error && (
        <p className="mt-3 text-sm text-destructive text-center animate-fade-in">{error}</p>
      )}
    </div>
  );
};

export default UploadZone;
