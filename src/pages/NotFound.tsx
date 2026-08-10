import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="text-center">
        <p className="mb-2 font-mono text-sm text-primary">404</p>
        <h1 className="mb-3 text-3xl font-semibold tracking-tight">Page not found</h1>
        <p className="mb-6 text-muted-foreground">That route does not exist in Deep Eye Vision.</p>
        <Link to="/" className="text-primary underline-offset-4 hover:underline">
          Back to detector
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
