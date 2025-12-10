// ReplaceGUIDwithCorrectOne.cpp : Patched and Optimized Version
//

#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>
#include <regex>
#include <map>
#include <set>

// Helper to remove potential carriage return from getline on Windows
std::string CleanPath(std::string path) {
    if (!path.empty() && path.back() == '\r') {
        path.pop_back();
    }
    return path;
}

std::string ReplaceSubstring(std::string string, std::string substring, std::string replaceWith)
{
    try {
        return std::regex_replace(string, std::regex(substring), replaceWith);
    } catch (...) {
        return string; // Fallback if regex fails
    }
}

int main()
{
    std::cout << "--- Unity GUID Fixer Tool v2.1 (Robust & Optimized) ---\n";

    try {
        std::string IncorrectGUIDsPath;
        std::string CorrectGUIDsPath;
        std::string UnityProjectPath;

        std::cout << "Give the path to the Incorrect guids (the package folder containing them) usually '/Assets/Scripts/[Package]'\n";
        std::getline(std::cin, IncorrectGUIDsPath);
        IncorrectGUIDsPath = CleanPath(IncorrectGUIDsPath);

        std::cout << "Give the path where the actual package is that usually being '/Library/PackageCache/[Package]'\n";
        std::getline(std::cin, CorrectGUIDsPath);
        CorrectGUIDsPath = CleanPath(CorrectGUIDsPath);

        std::cout << "Give the path to the Unity Project's 'Assets' folder '/Assets'\n";
        std::getline(std::cin, UnityProjectPath);
        UnityProjectPath = CleanPath(UnityProjectPath);

        std::filesystem::path path1 = IncorrectGUIDsPath;
        std::filesystem::path path2 = CorrectGUIDsPath;
        std::filesystem::path path3 = UnityProjectPath;

        if (!std::filesystem::exists(path1) || !std::filesystem::exists(path2) || !std::filesystem::exists(path3))
        {
            std::cout << "Error: One or more paths are invalid.\n";
            std::cout << "Path 1: " << path1 << " (" << std::filesystem::exists(path1) << ")\n";
            std::cout << "Path 2: " << path2 << " (" << std::filesystem::exists(path2) << ")\n";
            std::cout << "Path 3: " << path3 << " (" << std::filesystem::exists(path3) << ")\n";
            return 1;
        }

        // Optimization: Index the Correct GUIDs first
        // Map: Filename -> CorrectGUID
        std::cout << "Indexing Correct GUIDs from: " << path2.filename() << "...\n";
        std::map<std::string, std::string> correctGuidMap;

        for (const auto& entry : std::filesystem::recursive_directory_iterator(CorrectGUIDsPath))
        {
            if (!entry.is_regular_file() || entry.path().extension() != ".meta") continue;

            std::ifstream ifs(entry.path());
            if (!ifs.good()) continue;

            std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
            if (content.length() < 60) continue;

            std::string guid = content.substr(27, 32);
            correctGuidMap[entry.path().filename().string()] = guid;
        }
        std::cout << "Indexed " << correctGuidMap.size() << " correct meta files.\n";

        // Collect replacements
        struct Replacement {
            std::string filename;
            std::string badGuid;
            std::string goodGuid;
        };
        std::vector<Replacement> replacements;

        std::cout << "Scanning for Incorrect GUIDs in: " << path1.filename() << "...\n";
        for (const auto& entry : std::filesystem::recursive_directory_iterator(IncorrectGUIDsPath))
        {
            if (!entry.is_regular_file() || entry.path().extension() != ".meta") continue;

            std::string filename = entry.path().filename().string();
            
            // Check if we have a correct version of this file
            if (correctGuidMap.find(filename) == correctGuidMap.end()) continue;

            std::ifstream ifs(entry.path());
            if (!ifs.good()) continue;

            std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
            if (content.length() < 60) continue;

            std::string badGuid = content.substr(27, 32);
            std::string goodGuid = correctGuidMap[filename];

            if (badGuid != goodGuid) {
                replacements.push_back({filename, badGuid, goodGuid});
                std::cout << "Found match: " << filename << " (Bad: " << badGuid << " -> Good: " << goodGuid << ")\n";
            }
        }

        if (replacements.empty()) {
            std::cout << "No matching files found to fix.\n";
            return 0;
        }

        std::cout << "Found " << replacements.size() << " files to fix. Scanning Unity Project...\n";

        // Scan Unity Project ONCE (Optimization could be done here, but let's stick to safe iteration)
        // To be safe and simple: Iterate project files, and for each file, apply ALL replacements.
        // This is O(Files * Replacements) which is better than O(Files * Replacements) with file re-opening.
        
        int fixedFilesCount = 0;
        for (const auto& ProjectAssetFile : std::filesystem::recursive_directory_iterator(UnityProjectPath))
        {
            if (!ProjectAssetFile.is_regular_file()) continue;
            
            // Skip meta files? No, meta files also have references.
            // Skip known binary extensions to avoid reading huge files? 
            // .png, .jpg, .dll, .fbx usually don't have text references, but .prefab, .unity, .mat, .asset do.
            // Let's try to read all, but handle errors.

            try {
                std::ifstream ifs(ProjectAssetFile.path());
                if (!ifs.good()) continue;

                // Read file
                std::string content((std::istreambuf_iterator<char>(ifs)), (std::istreambuf_iterator<char>()));
                ifs.close();

                bool changed = false;
                for (const auto& rep : replacements) {
                    if (content.find(rep.badGuid) != std::string::npos) {
                        content = ReplaceSubstring(content, rep.badGuid, rep.goodGuid);
                        changed = true;
                    }
                }

                if (changed) {
                    std::ofstream ofs(ProjectAssetFile.path());
                    ofs << content;
                    std::cout << "Fixed references in: " << ProjectAssetFile.path().filename().string() << "\n";
                    fixedFilesCount++;
                }
            } catch (...) {
                // Ignore file read errors (permissions, locks, binaries)
                continue;
            }
        }

        std::cout << "Done! Fixed " << fixedFilesCount << " files.\n";

    } catch (const std::exception& e) {
        std::cerr << "CRITICAL ERROR: " << e.what() << "\n";
        return 1;
    } catch (...) {
        std::cerr << "UNKNOWN CRITICAL ERROR\n";
        return 1;
    }

    return 0;
}
