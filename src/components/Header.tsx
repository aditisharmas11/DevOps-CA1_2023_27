import { Eye } from "lucide-react";

const Header = () => {
  return (
    <header className="w-full pt-16 pb-8 px-4 text-center">
      <div className="inline-flex items-center justify-center gap-3 mb-4">
        <span className="flex h-11 w-11 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-primary">
          <Eye className="h-5 w-5" strokeWidth={1.75} />
        </span>
      </div>
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-semibold tracking-tight text-foreground">
        Deep Eye Vision
      </h1>
      <p className="mt-3 max-w-md mx-auto text-muted-foreground text-base sm:text-lg leading-relaxed">
        Upload a face image. We score authenticity and show where the model looked.
      </p>
    </header>
  );
};

export default Header;
