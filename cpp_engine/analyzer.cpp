#include <iostream>
#include <string>
#include <map>
#include <set>
#include <vector>
#include <cctype>
#include <cmath>
using namespace std;

set<string> stopwords = {
    "a", "an", "the", "is", "are", "of", "for", "and", "to", "with",
    "in", "on", "by", "as", "at", "from", "or", "that", "this", "experience",
    "skills", "projects", "education", "developed", "collaborated",
    "built", "develop", "team", "cross", "scalable", "concepts", "build", "database",
    "familiarity", "integrate", "knowledge"};

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
    {"databases", "database"}};

set<string> tokenize(string text)
{
    set<string> words;
    string word = "";

    for (char c : text)
    {
        if (isalpha(c))
        {
            word += tolower(c);
        }
        else
        {
            if (!word.empty())
            {
                if (!stopwords.count(word) && word.length() > 2)
                {
                    words.insert(normalize.count(word) ? normalize[word] : word);
                }
                word = "";
            }
        }
    }

    if (!word.empty())
    {
        if (!stopwords.count(word) && word.length() > 2)
        {
            words.insert(normalize.count(word) ? normalize[word] : word);
        }
    }

    return words;
}

map<string, int> freq(string text)
{
    map<string, int> f;
    string word = "";

    for (char c : text)
    {
        if (isalpha(c))
        {
            word += tolower(c);
        }
        else
        {
            if (!word.empty())
            {
                if (!stopwords.count(word) && word.length() > 2)
                {
                    f[normalize.count(word) ? normalize[word] : word]++;
                }
                word = "";
            }
        }
    }

    if (!word.empty())
    {
        if (!stopwords.count(word) && word.length() > 2)
        {
            f[normalize.count(word) ? normalize[word] : word]++;
        }
    }

    return f;
}

double cosine(map<string, int> &a, map<string, int> &b)
{
    double dot = 0, mag1 = 0, mag2 = 0;

    for (auto &p : a)
    {
        if (b.count(p.first))
            dot += p.second * b[p.first];
        mag1 += p.second * p.second;
    }

    for (auto &p : b)
    {
        mag2 += p.second * p.second;
    }

    return dot / (sqrt(mag1) * sqrt(mag2) + 1e-9);
}

double jaccard(const set<string> &a, const set<string> &b)
{
    int inter = 0;

    for (auto &w : a)
    {
        if (b.count(w))
            inter++;
    }

    int uni = a.size() + b.size() - inter;
    if (uni == 0)
        return 0;

    return (double)inter / uni;
}

vector<int> knapsackItems(vector<int> &val, vector<int> &wt, int W)
{
    int n = val.size();
    vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));

    for (int i = 1; i <= n; i++)
    {
        for (int w = 0; w <= W; w++)
        {
            if (wt[i - 1] <= w)
            {
                dp[i][w] = max(
                    val[i - 1] + dp[i - 1][w - wt[i - 1]],
                    dp[i - 1][w]);
            }
            else
            {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }

    vector<int> selected;
    int w = W;

    for (int i = n; i > 0; i--)
    {
        if (dp[i][w] != dp[i - 1][w])
        {
            selected.push_back(i - 1);
            w -= wt[i - 1];
        }
    }

    return selected;
}

int main()
{
    string education, skills, projects, experience, job, line;

    while (getline(cin, line))
    {
        if (line == "###")
            break;
        education += line + " ";
    }

    while (getline(cin, line))
    {
        if (line == "###")
            break;
        skills += line + " ";
    }

    while (getline(cin, line))
    {
        if (line == "###")
            break;
        projects += line + " ";
    }

    while (getline(cin, line))
    {
        if (line == "###")
            break;
        experience += line + " ";
    }

    while (getline(cin, line))
    {
        job += line + " ";
    }

    auto jobSet = tokenize(job);
    auto jobFreq = freq(job);

    auto calc = [&](string text)
    {
        auto tf = freq(text);
        double cos = cosine(tf, jobFreq);
        double jac = jaccard(tokenize(text), jobSet);
        return (0.7 * cos + 0.3 * jac) * 100;
    };

    double eduScore = calc(education);
    double skillScore = calc(skills);
    double projScore = calc(projects);
    double expScore = calc(experience);

    double finalScore =
        0.05 * eduScore +
        0.45 * skillScore +
        0.30 * projScore +
        0.20 * expScore;

    set<string> resumeAll = tokenize(education);
    auto temp = tokenize(skills);
    resumeAll.insert(temp.begin(), temp.end());
    temp = tokenize(projects);
    resumeAll.insert(temp.begin(), temp.end());
    temp = tokenize(experience);
    resumeAll.insert(temp.begin(), temp.end());

    vector<string> missing;
    for (auto &w : jobSet)
    {
        if (!resumeAll.count(w) && w.length() > 4)
        {
            missing.push_back(w);
        }
    }

    vector<int> val, wt;
    for (auto &w : missing)
    {
        val.push_back(jobFreq[w]);
        wt.push_back(w.length());
    }

    int capacity = 25;
    vector<int> selectedIdx = knapsackItems(val, wt, capacity);

    string level;
    if (finalScore > 75)
        level = "Excellent match";
    else if (finalScore > 50)
        level = "Good match";
    else if (finalScore > 30)
        level = "Average match";
    else
        level = "Poor match";

    cout << "Final Score: " << finalScore << "%\n\n";
    cout << "Match Quality: " << level << "\n\n";

    cout << "Breakdown:\n";
    cout << "Education: " << eduScore << "%\n";
    cout << "Skills: " << skillScore << "%\n";
    cout << "Projects: " << projScore << "%\n";
    cout << "Experience: " << expScore << "%\n\n";

    cout << "Missing Skills:\n";
    if (missing.empty())
    {
        cout << "- None (Good match)\n";
    }
    else
    {
        for (auto &w : missing)
        {
            cout << "- " << w << "\n";
        }
    }

    cout << "\nOptimized Skills to Add (Knapsack):\n";
    if (selectedIdx.empty())
    {
        cout << "- None\n";
    }
    else
    {
        for (int idx : selectedIdx)
        {
            cout << "- " << missing[idx] << "\n";
        }
    }

    cout << "\nSuggestions:\n";
    if (finalScore < 50)
    {
        cout << "- Add more relevant technical skills\n";
        cout << "- Include job-specific keywords\n";
    }
    else if (finalScore < 75)
    {
        cout << "- Improve project descriptions\n";
        cout << "- Add measurable achievements\n";
    }
    else
    {
        cout << "- Resume looks strong\n";
    }

    return 0;
}