// ReplaceGUIDwithCorrectOne.cpp : Standalone Batch Version with JSON Support (Fixes)
//

#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>
#include <regex>
#include <map>
#include <set>

struct FolderPair {
    std::string incorrectPath;
    std::string correctPath;
};

// Helper to remove potential carriage return from getline on Windows
std::string CleanPath(std::string path) {
    if (path.empty()) return "";
    
    // Remove trailing carriage return
    if (path.back() == '\r') {
        path.pop_back();
    }
    
    // Remove quotes if user added them
    if (path.length() >= 2 && path.front() == '"' && path.back() == '"') {
        path = path.substr(1, path.length() - 2);
    }
    
    // Trim whitespace
    const std::string whitespace = " \t\n\r";
    size_t first = path.find_first_not_of(whitespace);
    if (std::string::npos == first) {
        return "";
    }
    size_t last = path.find_last_not_of(whitespace);
    path = path.substr(first, (last - first + 1));
    
    // Normalize slashes to forward slashes for consistency
    for (char &c : path) {
        if (c == '\\') c = '/';
    }

    return path;
}

std::string ReplaceSubstring(std::string string, std::string substring, std::string replaceWith)
{
    try {
        size_t pos = 0;
        while ((pos = string.find(substring, pos)) != std::string::npos) {
             string.replace(pos, substring.length(), replaceWith);
             pos += replaceWith.length();
        }
        return string;
    } catch (...) {
        return string;
    }
}

// Simple JSON Parser
bool LoadFromJSON(const std::string& filename, std::vector<FolderPair>& outPairs, std::string& outUnityPath) {
    std::ifstream f(filename);
    if (!f.good()) {
        std::cerr << "Error: Could not open file " << filename << "\n";
        return false;
    }

    // Read entire file into string
    std::string content;
    f.seekg(0, std::ios::end);
    content.resize(f.tellg());
    f.seekg(0, std::ios::beg);
    f.read(&content[0], content.size());
    f.close();

    // 1. Find "unity_path"
    size_t uPathPos = content.find("\"unity_path\"");
    if (uPathPos != std::string::npos) {
        size_t colon = content.find(':', uPathPos);
        size_t quoteStart = content.find('"', colon + 1);
        size_t quoteEnd = content.find('"', quoteStart + 1);
        if (quoteStart != std::string::npos && quoteEnd != std::string::npos) {
            std::string path = content.substr(quoteStart + 1, quoteEnd - quoteStart - 1);
            if (!path.empty()) outUnityPath = CleanPath(path);
        }
    }

    // 2. Find "mappings" array
    size_t mapPos = content.find("\"mappings\"");
    if (mapPos == std::string::npos) {
        std::cerr << "Error: 'mappings' key not found in JSON.\n";
        return false;
    }

    size_t arrayStart = content.find('[', mapPos);
    if (arrayStart == std::string::npos) return false;

    // We are looking for structure: [ ["path1", "path2"], ["path3", "path4"] ]
    // We will scan character by character to handle nested arrays
    
    size_t i = arrayStart + 1;
    while (i < content.length()) {
        // Find start of a pair array '['
        size_t pairStart = content.find('[', i);
        size_t mainArrayEnd = content.find(']', i);

        // If we hit ']' before '[', we are done with the main array
        if (mainArrayEnd != std::string::npos && (pairStart == std::string::npos || mainArrayEnd < pairStart)) {
            break;
        }
        
        if (pairStart == std::string::npos) break;

        // Inside a pair [ "A", "B" ]
        size_t q1s = content.find('"', pairStart);
        size_t q1e = content.find('"', q1s + 1);
        
        size_t q2s = content.find('"', q1e + 1);
        size_t q2e = content.find('"', q2s + 1);
        
        size_t pairEnd = content.find(']', pairStart);

        if (q1s != std::string::npos && q1e != std::string::npos &&
            q2s != std::string::npos && q2e != std::string::npos &&
            pairEnd != std::string::npos && q2e < pairEnd) {
            
            std::string p1 = content.substr(q1s + 1, q1e - q1s - 1);
            std::string p2 = content.substr(q2s + 1, q2e - q2s - 1);
            
            outPairs.push_back({CleanPath(p1), CleanPath(p2)});
            
            i = pairEnd + 1;
        } else {
            // Something wrong with this pair, skip it
            i = pairStart + 1;
        }
    }
    
    return true;
}

int main()
{
    std::cout << "==================================================\n";
    std::cout << "   Unity GUID Fixer - Standalone Batch Mode v3.2  \n";
    std::cout << "==================================================\n\n";

    try {
        std::string UnityProjectPath;
        std::vector<FolderPair> pairs;
        
        // 1. Input Mode Selection
        std::cout << "Choose how to provide folder mappings:\n";
        std::cout << "1. Manual Entry\n";
        std::cout << "2. Load from 'mappings.txt' (Simple Text)\n";
        std::cout << "3. Load from 'mappings.json' (Generated by Python Tool)\n";
        std::cout << "Choice (1-3): ";
        
        std::string choice;
        std::getline(std::cin, choice);
        choice = CleanPath(choice);

        bool loaded = false;

        // Try to auto-detect JSON file in current directory for debugging
        std::string jsonPath = "mappings.json";
        if (!std::filesystem::exists(jsonPath)) {
            // Try looking one level up just in case
            if (std::filesystem::exists("../mappings.json")) jsonPath = "../mappings.json";
        }

        if (choice == "3") {
             std::cout << "Loading '" << jsonPath << "'...\n";
             if (std::filesystem::exists(jsonPath)) {
                 if (LoadFromJSON(jsonPath, pairs, UnityProjectPath)) {
                     std::cout << "Loaded " << pairs.size() << " pairs from JSON.\n";
                     if (!UnityProjectPath.empty()) {
                         std::cout << "Found Unity Path in JSON: " << UnityProjectPath << "\n";
                     }
                     loaded = true;
                 } else {
                     std::cout << "Failed to parse 'mappings.json'. Check format.\n";
                 }
             } else {
                 std::cout << "File '" << jsonPath << "' not found.\n";
                 std::cout << "Current working directory: " << std::filesystem::current_path() << "\n";
             }
        }
        else if (choice == "2") {
            std::ifstream f("mappings.txt");
            if (f.good()) {
                std::string line;
                while (std::getline(f, line)) {
                    line = CleanPath(line);
                    if (line.empty() || line[0] == '#') continue; 
                    size_t del = line.find('|');
                    if (del != std::string::npos) {
                        std::string p1 = CleanPath(line.substr(0, del));
                        std::string p2 = CleanPath(line.substr(del + 1));
                        if (!p1.empty() && !p2.empty()) pairs.push_back({p1, p2});
                    }
                }
                std::cout << "Loaded " << pairs.size() << " pairs from mappings.txt\n";
                loaded = true;
            } else {
                std::cout << "'mappings.txt' not found.\n";
            }
        }

        if (!loaded || pairs.empty()) {
            if (choice != "1") std::cout << "Switching to Manual Entry mode.\n";
            std::cout << "\n--- Manual Input Mode ---\n";
            while (true) {
                std::string p1, p2;
                std::cout << "\n[Pair #" << pairs.size() + 1 << "]\n";
                std::cout << "Path to OLD/INCORRECT folder:\n> ";
                std::getline(std::cin, p1);
                p1 = CleanPath(p1);
                if (p1 == "done" || p1.empty()) break;
                
                std::cout << "Path to NEW/CORRECT folder:\n> ";
                std::getline(std::cin, p2);
                p2 = CleanPath(p2);
                if (p2.empty()) continue;
                
                pairs.push_back({p1, p2});
            }
        }

        if (pairs.empty()) {
            std::cout << "No mappings provided. Exiting.\n";
            return 0;
        }

        // Validate Unity Path
        if (UnityProjectPath.empty() || !std::filesystem::exists(UnityProjectPath)) {
            while (true) {
                std::cout << "\nEnter the path to the Unity Project's 'Assets' folder:\n> ";
                std::getline(std::cin, UnityProjectPath);
                UnityProjectPath = CleanPath(UnityProjectPath);
                if (std::filesystem::exists(UnityProjectPath)) break;
                std::cout << "Error: Path does not exist.\n";
            }
        }

        // 3. Processing
        std::cout << "\n==================================================\n";
        std::cout << "Starting Batch Processing...\n";
        std::cout << "Target Project: " << UnityProjectPath << "\n";
        std::cout << "Total Pairs: " << pairs.size() << "\n";
        std::cout << "==================================================\n";

        // Global Map: OldGUID -> NewGUID
        std::map<std::string, std::string> globalGuidReplacementMap;
        int totalReplacementsFound = 0;

        for (size_t i = 0; i < pairs.size(); ++i) {
            std::cout << "Analyzing Pair " << i + 1 << "/" << pairs.size() << "...\n";
            std::string incorrectPath = pairs[i].incorrectPath;
            std::string correctPath = pairs[i].correctPath;

            if (!std::filesystem::exists(incorrectPath) || !std::filesystem::exists(correctPath)) {
                std::cout << "  Warning: One of the paths does not exist. Skipping.\n";
                // Debug info
                if (!std::filesystem::exists(incorrectPath)) std::cout << "    Missing: " << incorrectPath << "\n";
                if (!std::filesystem::exists(correctPath)) std::cout << "    Missing: " << correctPath << "\n";
                continue;
            }

            // Index Correct GUIDs
            std::map<std::string, std::string> correctGuidMap;
            for (const auto& entry : std::filesystem::recursive_directory_iterator(correctPath)) {
                if (!entry.is_regular_file() || entry.path().extension() != ".meta") continue;
                try {
                    std::ifstream ifs(entry.path());
                    if (!ifs.good()) continue;
                    std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
                    if (content.length() < 20) continue;
                    size_t guidPos = content.find("guid: ");
                    if (guidPos != std::string::npos && guidPos + 6 + 32 <= content.length()) {
                        std::string guid = content.substr(guidPos + 6, 32);
                        correctGuidMap[entry.path().filename().string()] = guid;
                    }
                } catch (...) { continue; }
            }

            // Find Mismatches
            int pairReplacements = 0;
            for (const auto& entry : std::filesystem::recursive_directory_iterator(incorrectPath)) {
                if (!entry.is_regular_file() || entry.path().extension() != ".meta") continue;
                try {
                    std::string filename = entry.path().filename().string();
                    if (correctGuidMap.find(filename) == correctGuidMap.end()) continue;

                    std::ifstream ifs(entry.path());
                    if (!ifs.good()) continue;
                    std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
                    if (content.length() < 20) continue;

                    size_t guidPos = content.find("guid: ");
                    if (guidPos != std::string::npos && guidPos + 6 + 32 <= content.length()) {
                        std::string oldGuid = content.substr(guidPos + 6, 32);
                        std::string newGuid = correctGuidMap[filename];
                        if (oldGuid != newGuid) {
                            globalGuidReplacementMap[oldGuid] = newGuid;
                            pairReplacements++;
                        }
                    }
                } catch (...) { continue; }
            }
            std::cout << "  Found " << pairReplacements << " GUIDs to fix in this pair.\n";
            totalReplacementsFound += pairReplacements;
        }

        std::cout << "\n--------------------------------------------------\n";
        std::cout << "Total Unique GUID Replacements collected: " << globalGuidReplacementMap.size() << "\n";
        
        if (globalGuidReplacementMap.empty()) {
            std::cout << "Nothing to fix. Exiting.\n";
            std::cout << "Press Enter to exit...";
            std::cin.ignore();
            std::cin.get();
            return 0;
        }

        std::cout << "Applying fixes to Unity Project... This may take a while.\n";
        
        int filesModified = 0;
        int replacementsMade = 0;
        int filesScanned = 0;

        for (const auto& ProjectAssetFile : std::filesystem::recursive_directory_iterator(UnityProjectPath))
        {
            if (!ProjectAssetFile.is_regular_file()) continue;
            std::string ext = ProjectAssetFile.path().extension().string();
            if (ext != ".prefab" && ext != ".unity" && ext != ".mat" && ext != ".asset" && ext != ".meta" && ext != ".playable") continue;

            filesScanned++;
            if (filesScanned % 100 == 0) std::cout << "Scanned " << filesScanned << " files...\r";

            try {
                std::ifstream ifs(ProjectAssetFile.path());
                if (!ifs.good()) continue;
                std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
                ifs.close();

                bool modified = false;
                std::string newContent = content;
                
                // Check if any old GUID exists in this file
                for (const auto& [oldGuid, newGuid] : globalGuidReplacementMap) {
                    if (newContent.find(oldGuid) != std::string::npos) {
                        newContent = ReplaceSubstring(newContent, oldGuid, newGuid);
                        modified = true;
                        replacementsMade++;
                    }
                }

                if (modified) {
                    std::ofstream ofs(ProjectAssetFile.path());
                    ofs << newContent;
                    ofs.close();
                    filesModified++;
                }
            } catch (...) { continue; }
        }

        std::cout << "\n\nDONE!\n";
        std::cout << "Files Modified: " << filesModified << "\n";
        std::cout << "Total Replacements: " << replacementsMade << "\n";

        // Deletion Logic
        std::cout << "\n--------------------------------------------------\n";
        std::cout << "Do you want to delete the OLD (Incorrect) folders now? (y/n): ";
        std::string delChoice;
        std::getline(std::cin, delChoice);

        if (!delChoice.empty() && (delChoice[0] == 'y' || delChoice[0] == 'Y')) {
            int deletedCount = 0;
            for (const auto& pair : pairs) {
                // Basic safety check: ensure we aren't deleting root or something obviously wrong
                if (pair.incorrectPath.length() < 3) {
                    std::cout << "Skipping dangerous path: " << pair.incorrectPath << "\n";
                    continue;
                }

                if (std::filesystem::exists(pair.incorrectPath)) {
                    try {
                        std::cout << "Deleting: " << pair.incorrectPath << "... ";
                        std::uintmax_t n = std::filesystem::remove_all(pair.incorrectPath);
                        std::cout << "Deleted (" << n << " items/files).\n";
                        deletedCount++;
                    }
                    catch (const std::filesystem::filesystem_error& e) {
                        std::cout << "Failed! " << e.what() << "\n";
                    }
                }
                else {
                    std::cout << "Skipping: " << pair.incorrectPath << " (Not found)\n";
                }
            }
            std::cout << "Deleted " << deletedCount << " folders.\n";
        }
        else {
            std::cout << "Skipped deletion.\n";
        }

        std::cout << "Press Enter to exit...";
        std::cin.get();

    } catch (const std::exception& e) {
        std::cerr << "CRITICAL ERROR: " << e.what() << "\n";
        std::cin.get();
        return 1;
    }

    return 0;
}
