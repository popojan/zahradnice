# Backlog Structure

This directory organizes feature proposals and implementation plans by status:

## 📁 Directories

### ✅ `completed/` 
Features that have been successfully implemented:
- `z-order-removal.md` - Visual layering system removed for simplicity
- `simplicity.md` - Language simplification through Z-order removal and program switching redesign  
- `unicode-support.md` - Full Unicode character support
- `multithreading.md` - Parallel rule execution system
- `infinite-cyclic-screen.md` - Toroidal screen wrapping via `#grid` directive

### ❌ `rejected/`
Features that have been rejected with documented rationale:
- `modular-programs.md` - Rejected for symbol semantic pollution
- `namespace-design-analysis.md` - Rejected as part of modular programs rejection
- `infinite-screen.md` - Rejected in favor of toroidal WYSIWYG approach

### ⏳ `pending/`
Features under consideration for future implementation:
- `demo-programs.md` - Comprehensive tutorial program suite
- `error-handling.md` - Fail-proof error handling strategy  
- `program-validation.md` - Grammar validation utility

### 📊 `analysis/`
Technical analysis documents (no implementation required):
- `screen-alternatives-comparison.md` - Comparison of screen system approaches

### 🔬 `research/`
Research documents exploring theoretical applications and advanced use cases:
- `gravity-simulation-ideas.md` - Physics simulation possibilities in toroidal space
- `theoretical-background.md` - Connections to L-systems, cellular automata theory
- `emergent-ai-coding.md` - Spatial AI and swarm intelligence implementation strategies
- `rl-opportunities.md` - Reinforcement learning research applications

## Status Indicators

Each document includes a clear status header:
- `COMPLETED ✅` - Feature implemented and documented
- `REJECTED` - Feature rejected with rationale
- No status indicator - Feature is pending consideration