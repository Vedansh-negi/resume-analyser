import React, { useState } from "react";
import "./App.css";

function App() {
  const [resume, setResume] = useState({
    education: "",
    skills: "",
    projects: "",
    experience: ""
  });

  const [job, setJob] = useState("");
  const [result, setResult] = useState("");

  const handleChange = (field, value) => {
    setResume({ ...resume, [field]: value });
  };
  const analyze = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          education: resume.education,
          skills: resume.skills,
          projects: resume.projects,
          experience: resume.experience,
          job: job
        })
      });

      const data = await res.json();
      console.log("Backend Response:", data);

      setResult(data.result || "No result returned");

    } catch (err) {
      console.error(err);
      setResult("❌ Backend error");
    }
  };

  return (
    <div className="app">

      {/* NAVBAR */}
      <nav className="navbar">
        <h2>ResumeAI</h2>
        <div>
          <button>Dashboard</button>
          <button>Templates</button>
          <button>Login</button>
        </div>
      </nav>

      {/* MAIN GRID */}
      <div className="main">

        {/* LEFT: RESUME BUILDER */}
        <div className="card">
          <h3>Build Your Resume</h3>

          <textarea
            placeholder="Education"
            onChange={(e) => handleChange("education", e.target.value)}
          />

          <textarea
            placeholder="Skills"
            onChange={(e) => handleChange("skills", e.target.value)}
          />

          <textarea
            placeholder="Projects"
            onChange={(e) => handleChange("projects", e.target.value)}
          />

          <textarea
            placeholder="Experience"
            onChange={(e) => handleChange("experience", e.target.value)}
          />
        </div>

        {/* RIGHT: JOB INPUT */}
        <div className="card">
          <h3>Job Description</h3>
          <textarea
            placeholder="Paste Job Description"
            onChange={(e) => setJob(e.target.value)}
          />

          <button className="analyze-btn" onClick={analyze}>
            Analyze Resume
          </button>
        </div>

      </div>

      {/* RESULT DASHBOARD */}
      <div className="result-card">
        <h2>Analysis Result</h2>
        <pre>{result || "No analysis yet"}</pre>
      </div>

    </div>
  );
}

export default App;
