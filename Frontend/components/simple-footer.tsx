export function SimpleFooter() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="container py-4 sm:py-6">
        <div className="text-center">
          <p className="text-sm text-gray-400">
            © {new Date().getFullYear()} Rea Travel Agency. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
