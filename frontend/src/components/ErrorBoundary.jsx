import { Component } from "react";
import { useLocale } from "../hooks/useLocale.js";

class ErrorBoundaryInner extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || "",
    };
  }

  componentDidCatch(error, errorInfo) {
    // Keep error details in console for debugging while showing fallback UI.
    console.error(this.props.copy.consoleLabel, error, errorInfo);
  }

  render() {
    const { copy } = this.props;
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, fontFamily: "Segoe UI, sans-serif" }}>
          <h2 style={{ marginTop: 0 }}>{copy.title}</h2>
          <p>{this.state.message || copy.unknownError}</p>
          <p>{copy.hint}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function ErrorBoundary(props) {
  const { copy } = useLocale();
  return <ErrorBoundaryInner {...props} copy={copy.errorBoundary} />;
}
