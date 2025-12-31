"use client";

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  companyName: string;
  onCompanyNameChange: (value: string) => void;
  jobTitle: string;
  onJobTitleChange: (value: string) => void;
  disabled: boolean;
}

export default function JobDescriptionInput({
  value,
  onChange,
  companyName,
  onCompanyNameChange,
  jobTitle,
  onJobTitleChange,
  disabled,
}: JobDescriptionInputProps) {
  return (
    <div className="w-full space-y-4">
      {/* Job Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Description
        </label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="Paste the full job description here..."
          rows={10}
          className={`
            w-full px-4 py-3 border rounded-lg resize-y
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            ${disabled ? "bg-gray-100 cursor-not-allowed" : "bg-white"}
            border-gray-300
          `}
        />
        <p className="mt-1 text-xs text-gray-500">
          {value.length.toLocaleString()} characters
        </p>
      </div>

      {/* Optional Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name{" "}
            <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            value={companyName}
            onChange={(e) => onCompanyNameChange(e.target.value)}
            disabled={disabled}
            placeholder="Auto-detected from job description"
            className={`
              w-full px-4 py-2 border rounded-lg
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${disabled ? "bg-gray-100 cursor-not-allowed" : "bg-white"}
              border-gray-300
            `}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Title{" "}
            <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            value={jobTitle}
            onChange={(e) => onJobTitleChange(e.target.value)}
            disabled={disabled}
            placeholder="Auto-detected from job description"
            className={`
              w-full px-4 py-2 border rounded-lg
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${disabled ? "bg-gray-100 cursor-not-allowed" : "bg-white"}
              border-gray-300
            `}
          />
        </div>
      </div>

      <p className="text-xs text-gray-500">
        Leave company name and job title empty to have them automatically extracted from the job description.
      </p>
    </div>
  );
}
