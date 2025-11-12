/**
 * Test suite for multi-page report generation and analysis result parsing.
 *
 * This module tests the parseMultiPageAnalysisResults function, ensuring:
 * 1. Correct multi-page report structure generation
 * 2. Proper status determination for different scenarios
 * 3. Handling of structured and string-based analysis
 * 4. Image references integration
 * 5. Edge cases and error handling
 *
 * The tests cover:
 * - Multi-page report structure validation
 * - Status determination logic for critical issues, visual changes, and recommendations
 * - String-based analysis fallback
 * - Image references handling
 * - Edge cases with missing or invalid data
 */

import { describe, it, expect } from "vitest";
import { parseMultiPageAnalysisResults } from "../../src/reporter/report-generator.js";

describe("parseMultiPageAnalysisResults", () => {
  it("should return correct basic structure", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "No issues found",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    // Test test_data structure
    expect(result).toBeInstanceOf(Object);
    expect(result.test_data.pr_number).toBe("123");
    expect(result.test_data.repository).toBe("test/repo");
    expect(typeof result.test_data.timestamp).toBe("string");

    // Test reports structure
    expect(result.reports).toHaveLength(1);
    const report = result.reports[0];
    expect(report.page_path).toBe("/");
    expect(report.url).toBe("https://example.com");
    expect(report.preview_url).toBe("https://preview.example.com");
    expect(report.status).toBe("pass");
  });

  it("should determine status as fail when critical issues are present", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues_enum: "missing_sections",
          critical_issues: {
            sections: [
              {
                name: "Header",
                status: "missing",
                description: "Header missing",
              },
            ],
            summary: "Missing critical sections",
          },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Missing sections detected",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("fail");
  });

  it("should determine status as warning when significant visual changes are present", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues_enum: "none",
          visual_changes_enum: "significant",
          recommendation_enum: "review_required",
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Significant changes detected",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("warning");
  });

  it("should determine status as warning when minor visual changes are present", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues_enum: "none",
          visual_changes_enum: "minor",
          recommendation_enum: "pass",
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Minor changes detected",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("warning");
  });

  it("should handle string-based analysis fallback", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: "Found missing sections in the layout" as any,
        sections_analysis: "String-based analysis",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("fail");
  });

  it("should handle string-based analysis with significant changes", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: "Found significant changes in the layout" as any,
        sections_analysis: "String-based analysis",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("warning");
  });

  it("should handle string-based analysis with no issues", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: "No significant changes detected" as any,
        sections_analysis: "String-based analysis",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.status).toBe("pass");
  });

  it("should process multiple pages with different statuses", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues_enum: "none",
          visual_changes_enum: "minor",
          recommendation_enum: "pass",
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Page 1 analysis",
      },
      {
        page_path: "/about",
        base_url: "https://example.com/about",
        pr_url: "https://preview.example.com/about",
        visual_analysis: {
          critical_issues_enum: "missing_sections",
          visual_changes_enum: "none",
          recommendation_enum: "review_required",
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Page 2 analysis",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    expect(result.reports).toHaveLength(2);
    expect(result.reports[0].status).toBe("warning"); // minor changes
    expect(result.reports[1].status).toBe("fail"); // critical issues
  });

  it("should handle image references", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Analysis with images",
        image_refs: {
          base_screenshot: "base64_encoded_image_1",
          pr_screenshot: "base64_encoded_image_2",
          diff_image: "base64_encoded_image_3",
        },
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.image_refs).not.toBeNull();
    expect(report.image_refs?.base_screenshot).toBe("base64_encoded_image_1");
    expect(report.image_refs?.pr_screenshot).toBe("base64_encoded_image_2");
    expect(report.image_refs?.diff_image).toBe("base64_encoded_image_3");
  });

  it("should handle missing image references", () => {
    const pageResults = [
      {
        page_path: "/",
        base_url: "https://example.com",
        pr_url: "https://preview.example.com",
        visual_analysis: {
          critical_issues: { sections: [], summary: "" },
          structural_analysis: {
            section_order: "",
            layout: "",
            broken_layouts: "",
          },
          visual_changes: {
            diff_highlights: [],
            animation_issues: "",
            conclusion: "",
          },
          conclusion: {
            critical_issues: "",
            visual_changes: "",
            recommendation: "",
            summary: "",
          },
        },
        sections_analysis: "Analysis without images",
      },
    ];

    const result = parseMultiPageAnalysisResults(
      "123",
      "test/repo",
      pageResults
    );

    const report = result.reports[0];
    expect(report.image_refs).toBeNull();
  });

  it("should handle empty page results list", () => {
    const result = parseMultiPageAnalysisResults("123", "test/repo", []);

    expect(result).toBeInstanceOf(Object);
    expect(result.test_data.pr_number).toBe("123");
    expect(result.test_data.repository).toBe("test/repo");
    expect(result.reports).toHaveLength(0);
  });

  it("should handle complex status determination logic", () => {
    const testCases: Array<{
      critical_issues_enum: string;
      visual_changes_enum: string;
      recommendation_enum: string;
      expected_status: string;
    }> = [
      {
        critical_issues_enum: "none",
        visual_changes_enum: "none",
        recommendation_enum: "pass",
        expected_status: "pass",
      },
      {
        critical_issues_enum: "missing_sections",
        visual_changes_enum: "none",
        recommendation_enum: "pass",
        expected_status: "fail",
      },
      {
        critical_issues_enum: "other_issues",
        visual_changes_enum: "none",
        recommendation_enum: "pass",
        expected_status: "fail",
      },
      {
        critical_issues_enum: "none",
        visual_changes_enum: "significant",
        recommendation_enum: "pass",
        expected_status: "warning",
      },
      {
        critical_issues_enum: "none",
        visual_changes_enum: "minor",
        recommendation_enum: "pass",
        expected_status: "warning",
      },
      {
        critical_issues_enum: "none",
        visual_changes_enum: "none",
        recommendation_enum: "review_required",
        expected_status: "warning",
      },
      {
        critical_issues_enum: "none",
        visual_changes_enum: "significant",
        recommendation_enum: "review_required",
        expected_status: "warning",
      },
    ];

    for (const testCase of testCases) {
      const pageResults = [
        {
          page_path: "/",
          base_url: "https://example.com",
          pr_url: "https://preview.example.com",
          visual_analysis: {
            critical_issues_enum: testCase.critical_issues_enum,
            visual_changes_enum: testCase.visual_changes_enum,
            recommendation_enum: testCase.recommendation_enum,
            critical_issues: { sections: [], summary: "" },
            structural_analysis: {
              section_order: "",
              layout: "",
              broken_layouts: "",
            },
            visual_changes: {
              diff_highlights: [],
              animation_issues: "",
              conclusion: "",
            },
            conclusion: {
              critical_issues: "",
              visual_changes: "",
              recommendation: "",
              summary: "",
            },
          },
          sections_analysis: `Test case: ${testCase.critical_issues_enum}, ${testCase.visual_changes_enum}, ${testCase.recommendation_enum}`,
        },
      ];

      const result = parseMultiPageAnalysisResults(
        "123",
        "test/repo",
        pageResults
      );

      const report = result.reports[0];
      expect(report.status).toBe(testCase.expected_status);
    }
  });
});
