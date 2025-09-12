#pragma once

#include <string>

class StatusLineRenderer {
public:
    // Initialize template system for a new program
    static void initialize_program(const std::wstring& template_str, const std::wstring& help_text);
    
    // Render the complete status line (left content only, rule display handled separately)
    static std::string render(int score, int steps, int moves, int parallel_pct = -1);
    
    // Get current help text for display
    static std::wstring get_current_help();
    
    // Reset template system (for program restarts)
    static void reset();

private:
    static std::wstring active_template;
    static std::wstring current_help_text;
    static bool template_locked;
    
    // Helper function for string replacement
    static void replace_all(std::string &str, const std::string &from, const std::string &to);
    
    // Get the effective template (custom or default)
    static std::string get_effective_template();
};
