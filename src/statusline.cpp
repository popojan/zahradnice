#include "statusline.h"

// Static member definitions
std::wstring StatusLineRenderer::active_template = L"";
std::wstring StatusLineRenderer::current_help_text = L"";
bool StatusLineRenderer::template_locked = false;

void StatusLineRenderer::initialize_program(const std::wstring& template_str, const std::wstring& help_text) {
    // Update help text (always local to current program)
    current_help_text = help_text;
    
    // Update template only if not locked or if this program has a template
    if (!template_locked || !template_str.empty()) {
        if (!template_str.empty()) {
            active_template = template_str;
            template_locked = true;  // Lock inheritance for subroutines
        }
        // If template_str is empty and not locked, inherit current active_template
    }
}

std::string StatusLineRenderer::render(int score, int steps, int moves, int parallel_pct) {
    std::string tmpl = get_effective_template();
    
    // Perform variable substitutions
    replace_all(tmpl, "{score}", std::to_string(score));
    replace_all(tmpl, "{steps}", std::to_string(steps));
    replace_all(tmpl, "{moves}", std::to_string(moves));
    
    // Add parallel percentage if available (>= 0)
    if (parallel_pct >= 0) {
        replace_all(tmpl, "{parallel}", "(" + std::to_string(parallel_pct) + "%)");
    } else {
        replace_all(tmpl, "{parallel}", "");
    }
    
    // Convert help text to string for substitution
    std::string help_str(current_help_text.begin(), current_help_text.end());
    replace_all(tmpl, "{help}", help_str);
    
    return tmpl;
}

std::wstring StatusLineRenderer::get_current_help() {
    return current_help_text;
}

void StatusLineRenderer::reset() {
    active_template = L"";
    current_help_text = L"";
    template_locked = false;
}

void StatusLineRenderer::replace_all(std::string &str, const std::string &from, const std::string &to) {
    size_t start_pos = 0;
    while ((start_pos = str.find(from, start_pos)) != std::string::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length();
    }
}

std::string StatusLineRenderer::get_effective_template() {
    if (!active_template.empty()) {
        // Use active template
        std::string result(active_template.begin(), active_template.end());
        return result;
    } else {
        // Use reasonable default template
        return "Score: {score} Steps: {steps} {parallel} {help}";
    }
}