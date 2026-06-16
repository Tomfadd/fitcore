import { Component } from 'react';

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 60, textAlign: 'center', background: '#080c10', minHeight: '100vh', color: '#e8f4f8' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <h2 style={{ fontFamily: 'sans-serif', color: '#ff4757', marginBottom: 8 }}>Something went wrong</h2>
          <p style={{ color: '#6b8599', marginBottom: 28, fontSize: 13 }}>{this.state.error?.message}</p>
          <button
            style={{ padding: '12px 28px', background: '#00e5ff', color: '#000', border: 'none', borderRadius: 10, cursor: 'pointer', fontFamily: 'sans-serif', fontWeight: 700, fontSize: 15 }}
            onClick={() => window.location.reload()}
          >
            Reload App
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
