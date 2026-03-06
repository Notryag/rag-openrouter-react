import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || "Unknown frontend error",
    };
  }

  componentDidCatch(error, errorInfo) {
    // Keep error details in console for debugging while showing fallback UI.
    console.error("Frontend render error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, fontFamily: "Segoe UI, sans-serif" }}>
          <h2 style={{ marginTop: 0 }}>Frontend crashed</h2>
          <p>{this.state.message}</p>
          <p>Open browser DevTools Console to view stack trace.</p>
        </div>
      );
    }
    return this.props.children;
  }
}
