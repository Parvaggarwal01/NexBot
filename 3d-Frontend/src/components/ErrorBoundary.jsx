import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.log("Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-full bg-gradient-to-br from-red-900/20 to-purple-900/20">
          <div className="text-center p-8 bg-black/50 backdrop-blur-sm rounded-2xl border border-red-500/20">
            <div className="text-6xl mb-4">🤖❌</div>
            <h2 className="text-2xl font-bold text-red-400 mb-2">
              Robot Malfunction
            </h2>
            <p className="text-gray-300 mb-4">
              The AI assistant encountered an error and needs to be reset.
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Reset Robot
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
