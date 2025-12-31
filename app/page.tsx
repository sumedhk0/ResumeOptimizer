"use client";

import { useState } from "react";
import ResumeUploader from "@/components/ResumeUploader";
import JobDescriptionInput from "@/components/JobDescriptionInput";
import ProgressIndicator, { ProgressStep } from "@/components/ProgressIndicator";

export default function Home() {
  // Form state
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");

  // Progress state
  const [currentStep, setCurrentStep] = useState<ProgressStep>("idle");
  const [error, setError] = useState<string | null>(null);

  // Result state
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [downloadFilename, setDownloadFilename] = useState<string>("");
  const [keywordsAdded, setKeywordsAdded] = useState<string[]>([]);

  const isFormValid = resumeFile && jobDescription.trim().length > 50;
  const isProcessing = currentStep !== "idle" && currentStep !== "complete" && currentStep !== "error";

  const handleSubmit = async () => {
    if (!resumeFile || !jobDescription) return;

    // Reset state
    setError(null);
    setDownloadUrl(null);
    setKeywordsAdded([]);

    try {
      // Step 1: Upload
      setCurrentStep("uploading");

      const formData = new FormData();
      formData.append("resume", resumeFile);
      formData.append("job_description", jobDescription);
      if (companyName) formData.append("company_name", companyName);
      if (jobTitle) formData.append("job_title", jobTitle);

      // Step 2-5: Processing (shown progressively)
      setCurrentStep("extracting");

      // Simulate progress steps while waiting for API
      const progressTimeout = setTimeout(() => setCurrentStep("analyzing"), 2000);
      const progressTimeout2 = setTimeout(() => setCurrentStep("tailoring"), 5000);
      const progressTimeout3 = setTimeout(() => setCurrentStep("generating"), 15000);

      const response = await fetch("/api/generate", {
        method: "POST",
        body: formData,
      });

      // Clear progress timeouts
      clearTimeout(progressTimeout);
      clearTimeout(progressTimeout2);
      clearTimeout(progressTimeout3);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate resume");
      }

      // Get keywords from header
      const keywords = response.headers.get("X-Keywords-Added");
      if (keywords) {
        setKeywordsAdded(keywords.split(",").filter(Boolean));
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "Resume_Tailored.pdf";
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }
      setDownloadFilename(filename);

      // Create blob URL for download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);

      setCurrentStep("complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setCurrentStep("error");
    }
  };

  const handleReset = () => {
    // Revoke old blob URL to free memory
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
    }

    setResumeFile(null);
    setJobDescription("");
    setCompanyName("");
    setJobTitle("");
    setCurrentStep("idle");
    setError(null);
    setDownloadUrl(null);
    setKeywordsAdded([]);
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <main className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            ATS Resume Optimizer
          </h1>
          <p className="mt-3 text-lg text-gray-600">
            Generate an ATS-optimized resume tailored to your target job using AI
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-white shadow-lg rounded-xl p-6 sm:p-8 space-y-8">
          {/* Form */}
          {currentStep === "idle" && (
            <>
              <ResumeUploader
                onFileSelect={setResumeFile}
                selectedFile={resumeFile}
                disabled={isProcessing}
              />

              <JobDescriptionInput
                value={jobDescription}
                onChange={setJobDescription}
                companyName={companyName}
                onCompanyNameChange={setCompanyName}
                jobTitle={jobTitle}
                onJobTitleChange={setJobTitle}
                disabled={isProcessing}
              />

              {/* Submit Button */}
              <button
                onClick={handleSubmit}
                disabled={!isFormValid || isProcessing}
                className={`
                  w-full py-3 px-6 rounded-lg text-white font-medium text-lg
                  transition-all duration-200
                  ${
                    isFormValid && !isProcessing
                      ? "bg-blue-600 hover:bg-blue-700 cursor-pointer"
                      : "bg-gray-300 cursor-not-allowed"
                  }
                `}
              >
                Generate Tailored Resume
              </button>

              {!isFormValid && resumeFile && (
                <p className="text-sm text-gray-500 text-center">
                  Please enter a job description (at least 50 characters)
                </p>
              )}
            </>
          )}

          {/* Progress */}
          {(isProcessing || currentStep === "error") && (
            <ProgressIndicator currentStep={currentStep} error={error} />
          )}

          {/* Error - Retry Button */}
          {currentStep === "error" && (
            <div className="flex gap-4">
              <button
                onClick={handleReset}
                className="flex-1 py-3 px-6 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              >
                Start Over
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 py-3 px-6 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Success - Download */}
          {currentStep === "complete" && downloadUrl && (
            <div className="space-y-6">
              <ProgressIndicator currentStep={currentStep} />

              {/* Keywords Added */}
              {keywordsAdded.length > 0 && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm font-medium text-blue-800 mb-2">
                    ATS Keywords Added:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {keywordsAdded.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Download Button */}
              <button
                onClick={handleDownload}
                className="w-full py-4 px-6 rounded-lg bg-green-600 text-white font-medium text-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download Resume
              </button>

              {/* Generate Another */}
              <button
                onClick={handleReset}
                className="w-full py-3 px-6 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              >
                Generate Another Resume
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-gray-500">
          Your resume is processed securely and not stored on our servers.
        </p>
      </div>
    </main>
  );
}
