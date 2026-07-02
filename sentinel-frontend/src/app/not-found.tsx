import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex h-[80vh] flex-col items-center justify-center text-center px-4">
      <ShieldQuestion className="mb-6 h-16 w-16 text-muted-foreground" />
      <h2 className="mb-2 text-3xl font-bold">404 - Page Not Found</h2>
      <p className="mb-8 text-muted-foreground max-w-md">
        The page you are looking for does not exist or has been moved. 
        If you are looking for an execution session, it may have expired.
      </p>
      <Button asChild>
        <Link href="/">Return Home</Link>
      </Button>
    </div>
  );
}
