#include <iostream>
#include <string>
#include <map>
#include <set>
#include <vector>
#include <cctype>
#include <cmath>
using namespace std;

set<string> stopwords = {
    "a","an","the","is","are","of","for","and","to","with",
    "in","on","by","as","at","from","or","that","this"
};

map<string, string> normalize = {
    {"develop", "build"},
{"built", "build"},
{"developed", "build"},
{"collaborate", "team"},
{"team", "team"},
{"cross", "team"},
{"scalable", "system"},
{"backend", "api"},
{"apis", "api"},
{"database", "database"},
{"databases", "database"}
};
set<string> tokenize(string text){
    set<string> words;
    string word = "";
    for(char c : text){
        if(isalpha(c)){
            word += tolower(c);
        } else {
            if(!word.empty()){
                if(!stopwords.count(word) && word.length() > 2){
                    if(normalize.count(word))
                        words.insert(normalize[word]);
                    else
                        words.insert(word);
                }
                word = "";
            }
        }
    }
    if(!word.empty()){
    if(!stopwords.count(word) && word.length() > 2){
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
map<string,int> freq(string text){
    map<string,int> f;
    string word = "";
    for(char c : text){
        if(isalpha(c)){
            word += tolower(c);
        } else {
            if(!word.empty()){
                if(!stopwords.count(word) && word.length() > 2){
                    if(normalize.count(word))
                        f[normalize[word]]++;
                    else
                        f[word]++;
                }
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
double cosine(map<string,int>& a, map<string,int>& b){
    double dot = 0, mag1 = 0, mag2 = 0;
    for(auto &p : a){
        if(b.count(p.first))
            dot += p.second * b[p.first];
        mag1 += p.second * p.second;
    }
    for(auto &p : b){
        mag2 += p.second * p.second;
    }
    return dot / (sqrt(mag1) * sqrt(mag2) + 1e-9);
}
double jaccard(const set<string>& a, const set<string>& b){
    int inter = 0;
    for(auto &w : a){
        if(b.count(w)) inter++;
    }
    int uni = a.size() + b.size() - inter;
    if(uni == 0) return 0;

    return (double)inter / uni;
}

double calculateScore(string text, string job){
    auto tset = tokenize(text);
    auto jset = tokenize(job);

    auto tf = freq(text);
    auto jf = freq(job);

    double cos = cosine(tf, jf);
    double jac = jaccard(tset, jset);

    return (0.7 * cos + 0.3 * jac) * 100;
}

int main(){
    string education, skills, projects, experience, job, line;

    while(getline(cin, line)){
        if(line == "###") break;
        education += line + " ";
    }

    while(getline(cin, line)){
        if(line == "###") break;
        skills += line + " ";
    }

    while(getline(cin, line)){
        if(line == "###") break;
        projects += line + " ";
    }

    while(getline(cin, line)){
        if(line == "###") break;
        experience += line + " ";
    }

    while(getline(cin, line)){
        job += line + " ";
    }

    auto jobSet = tokenize(job);

    auto eduSet = tokenize(education);
    auto skillSet = tokenize(skills);
    auto projSet = tokenize(projects);
    auto expSet = tokenize(experience);

    auto calc = [&](string text){
        auto tf = freq(text);
        auto jf = freq(job);

        double cos = cosine(tf, jf);
        double jac = jaccard(tokenize(text), jobSet);

        return (0.7 * cos + 0.3 * jac) * 100;
    };

    double eduScore = calc(education);
    double skillScore = calc(skills);
    double projScore = calc(projects);
    double expScore = calc(experience);

    double finalScore =
    0.05 * eduScore+     
    0.45 * skillScore +
    0.30 * projScore +
    0.20 * expScore;
    set<string> resumeAll = eduSet;
    resumeAll.insert(skillSet.begin(), skillSet.end());
    resumeAll.insert(projSet.begin(), projSet.end());
    resumeAll.insert(expSet.begin(), expSet.end());

    vector<string> missing;

    for(auto &w : jobSet){
        if(!resumeAll.count(w) && w.length() > 4 && isalpha(w[0])){
            missing.push_back(w);
        }
    }

    if(missing.size() > 5) missing.resize(5);

    string level;
    if(finalScore > 75) level = "Excellent match";
    else if(finalScore > 50) level = "Good match";
    else if(finalScore > 30) level = "Average match";
    else level = "Poor match";
    cout << "Final Score: " << finalScore << "%\n\n";

    cout << "Match Quality: " << level << "\n\n";

    cout << "Breakdown:\n";
    cout << "Education: " << eduScore << "%\n";
    cout << "Skills: " << skillScore << "%\n";
    cout << "Projects: " << projScore << "%\n";
    cout << "Experience: " << expScore << "%\n\n";

    cout << "Missing Skills:\n";
    if(missing.empty()){
        cout << "- None (Good match)\n";
    } else {
        for(auto &w : missing){
            cout << "- " << w << "\n";
        }
    }
    cout << "\nSuggestions:\n";

    if(finalScore < 50){
        cout << "- Add more relevant technical skills\n";
        cout << "- Include job-specific keywords\n";
    }
    else if(finalScore < 75){
        cout << "- Improve project descriptions\n";
        cout << "- Add measurable achievements\n";
    }
    else{
        cout << "- Resume looks strong\n";
    }
    return 0;
}
