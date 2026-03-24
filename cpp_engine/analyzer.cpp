#include <iostream>
#include <string>
#include <map>
#include <set>
#include <vector>
#include <cctype>
#include <cmath>
using namespace std;

// ---------------- STOPWORDS ----------------
set<string> stopwords = {
    "a","an","the","is","are","of","for","and","to","with",
    "in","on","by","as","at","from","or","that","this",
    "using","built","plus","relevant","coursework","experience",
    "looking","need","knowledge","developer"
};
map<string, string> normalize = {
    {"mysql", "database"},
    {"postgresql", "database"},
    {"mongodb", "database"},
    {"fastapi", "api"},
    {"rest", "api"},
    {"restapi", "api"},
    {"oop", "concept"},
    {"oops", "concept"},
    {"objectoriented", "concept"},
    {"javascript", "js"}
};
// ---------------- TOKENIZE ----------------
set<string> tokenize(string text){
    set<string> words;
    string word = "";

    for(char c : text){
        if(isalpha(c)){
            word += tolower(c);
        } else {
            if(!word.empty()){
                if(!stopwords.count(word) && word.length() > 2){
                    words.insert(word);
                }
                word = "";
            }
        }
    }

    if(!word.empty()){
    if(!stopwords.count(word) && word.length() > 2){

        // normalize word
        if(normalize.count(word)){
            words.insert(normalize[word]);
        } else {
            words.insert(word);
        }
    }
    word = "";
}

    return words;
}

// ---------------- FREQUENCY ----------------
map<string,int> freq(string text){
    map<string,int> f;
    string word = "";

    for(char c : text){
        if(isalnum(c)){
            word += tolower(c);
        } else {
            if(!word.empty()){
                f[word]++;
                word = "";
            }
        }
    }

    if(normalize.count(word)){
    f[normalize[word]]++;
} else {
    f[word]++;
}

    return f;
}

// ---------------- COSINE ----------------
double cosine(map<string,int>& a, map<string,int>& b){
    double dot = 0, mag1 = 0, mag2 = 0;

    for(auto &p : a){
        dot += p.second * b[p.first];
        mag1 += p.second * p.second;
    }

    for(auto &p : b){
        mag2 += p.second * p.second;
    }

    return dot / (sqrt(mag1) * sqrt(mag2) + 1e-9);
}

// ---------------- JACCARD ----------------
double jaccard(set<string>& a, set<string>& b){
    int inter = 0;

    for(auto &w : a){
        if(b.count(w)) inter++;
    }

    int uni = a.size() + b.size() - inter;
    return (double)inter / uni;
}

// ---------------- MAIN ----------------
int main(){
    string resume, job;

    // SIMPLE INPUT (IMPORTANT)
    string line;

// Read resume until ###
while(getline(cin, line)){
    if(line == "###") break;
    resume += line + " ";
}

// Read job description
while(getline(cin, line)){
    job += line + " ";
}

    auto rset = tokenize(resume);
    auto jset = tokenize(job);

    auto rf = freq(resume);
    auto jf = freq(job);

    double cos = cosine(rf, jf);
    double jac = jaccard(rset, jset);

    double score = (cos + jac) / 2 * 100;

    // ---------------- IMPORTANT MISSING SKILLS ----------------
    vector<string> importantMissing;

    for(auto &w : jset){
        if(!rset.count(w) && w.length() > 3 && !stopwords.count(w)){
            importantMissing.push_back(w);
        }
    }

    // limit to top 5
    if(importantMissing.size() > 5){
        importantMissing.resize(5);
    }

    // ---------------- MATCH LEVEL ----------------
    string level;

    if(score > 75) level = "Excellent match";
    else if(score > 50) level = "Good match";
    else if(score > 30) level = "Average match";
    else level = "Poor match";

    // ---------------- OUTPUT ----------------
    cout << "Resume Score: " << score << "%\n\n";

    cout << "Match Quality: " << level << "\n\n";

    cout << "Missing Key Skills:\n";
    if(importantMissing.empty()){
        cout << "- None (Good match)\n";
    } else {
        for(auto &w : importantMissing){
            cout << "- " << w << "\n";
        }
    }

    cout << "\nSuggestions:\n";

    if(score < 50){
        cout << "- Add more relevant technical skills\n";
        cout << "- Include job-related keywords\n";
    }
    else if(score < 75){
        cout << "- Improve project descriptions\n";
        cout << "- Add measurable achievements\n";
    }
    else{
        cout << "- Resume looks strong\n";
    }
cout << "DEBUG RESUME: " << resume << endl;
cout << "DEBUG JOB: " << job << endl;
    return 0;
}