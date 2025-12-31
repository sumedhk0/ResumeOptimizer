"use client";

export type ProgressStep =
  | "idle"
  | "uploading"
  | "extracting"
  | "analyzing"
  | "tailoring"
  | "generating"
  | "complete"
  | "error";

interface ProgressIndicatorProps {
  currentStep: ProgressStep;
  error?: string | null;
}

const steps: { key: ProgressStep; label: string }[] = [
  { key: "uploading", label: "Uploading resume" },
  { key: "extracting", label: "Extracting content" },
  { key: "analyzing", label: "Analyzing job description" },
  { key: "tailoring", label: "Tailoring with AI" },
  { key: "generating", label: "Generating PDF" },
];

export default function ProgressIndicator({
  currentStep,
  error,
}: ProgressIndicatorProps) {
  if (currentStep === "idle") {
    return null;
  }

  const getStepStatus = (step: ProgressStep): "pending" | "active" | "complete" => {
    const stepOrder = steps.map((s) => s.key);
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(step);

    if (currentStep === "complete") {
      return "complete";
    }
    if (currentStep === "error") {
      if (stepIndex < currentIndex) return "complete";
      if (stepIndex === currentIndex) return "active";
      return "pending";
    }
    if (stepIndex < currentIndex) return "complete";
    if (stepIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <div className="w-full bg-white rounded-lg border border-gray-200 p-6">
      {currentStep === "error" && error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">Error</span>
          </div>
          <p className="mt-2 text-sm text-red-600">{error}</p>
        </div>
      )}

      {currentStep === "complete" && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 text-green-700">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">Resume generated successfully!</span>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step.key);
          const isLast = index === steps.length - 1;

          return (
            <div key={step.key} className="flex items-start gap-4">
              {/* Step indicator */}
              <div className="flex flex-col items-center">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center
                    ${status === "complete" ? "bg-green-500" : ""}
                    ${status === "active" ? "bg-blue-500" : ""}
                    ${status === "pending" ? "bg-gray-200" : ""}
                  `}
                >
                  {status === "complete" && (
                    <svg
                      className="h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                  {status === "active" && (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  )}
                  {status === "pending" && (
                    <span className="text-gray-400 text-sm font-medium">
                      {index + 1}
                    </span>
                  )}
                </div>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={`
                      w-0.5 h-8 mt-1
                      ${status === "complete" ? "bg-green-500" : "bg-gray-200"}
                    `}
                  />
                )}
              </div>

              {/* Step label */}
              <div className="pt-1">
                <p
                  className={`
                    text-sm font-medium
                    ${status === "complete" ? "text-green-600" : ""}
                    ${status === "active" ? "text-blue-600" : ""}
                    ${status === "pending" ? "text-gray-400" : ""}
                  `}
                >
                  {step.label}
                  {status === "active" && "..."}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
