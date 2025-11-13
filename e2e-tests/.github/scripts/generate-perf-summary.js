#!/usr/bin/env node

/**
 * Generate performance summary from stress test results
 * Usage: node generate-perf-summary.js <perf-json-path> [--format=github|pr-comment]
 */

const fs = require('fs');
const path = require('path');

function generatePerfSummary(perfPath, format = 'github') {
  if (!fs.existsSync(perfPath)) {
    return format === 'github'
      ? '## ⚠️ E2E Stress Test Results\n\nPerformance data not found'
      : '## ⚠️ E2E Stress Test Results\n\nPerformance data not found. See workflow logs for details.\n';
  }

  let perfData;
  try {
    perfData = JSON.parse(fs.readFileSync(perfPath, 'utf8'));
  } catch (error) {
    return format === 'github'
      ? `## ⚠️ E2E Stress Test Results\n\nFailed to parse performance data: ${error.message}`
      : `## ⚠️ E2E Stress Test Results\n\nFailed to parse performance data. See workflow logs for details.\n`;
  }
  let summary = format === 'github'
    ? '## 📊 E2E Stress Test Performance\n\n'
    : '## 📊 E2E Stress Test Performance\n\n';

  // Status section
  if (perfData.error) {
    summary += `❌ **Status**: ERROR - ${perfData.error}\n\n`;
  } else if (perfData.expectedRuns && perfData.numRuns < perfData.expectedRuns) {
    summary += `⚠️ **Status**: INCOMPLETE - Only ${perfData.numRuns}/${perfData.expectedRuns} runs completed\n\n`;
  } else if (perfData.passed) {
    summary += `✅ **Status**: PASSED (${perfData.maxTime}ms max < ${perfData.maxAllowed}ms limit)\n\n`;
  } else {
    summary += `❌ **Status**: FAILED (${perfData.maxTime}ms max >= ${perfData.maxAllowed}ms limit)\n\n`;
  }

  // Summary table (only if we have data)
  if (perfData.numRuns > 0) {
    summary += '| Metric | Value |\n';
    summary += '|--------|-------|\n';
    summary += `| **Average Time** | ${perfData.avgTime}ms |\n`;
    summary += `| **Minimum Time** | ${perfData.minTime}ms |\n`;
    summary += `| **Maximum Time** | ${perfData.maxTime}ms |\n`;

    if (format === 'github') {
      summary += `| **Number of Runs** | ${perfData.numRuns} |\n`;
    } else {
      summary += `| **Completed Runs** | ${perfData.numRuns}${perfData.expectedRuns ? '/' + perfData.expectedRuns : ''} |\n`;
    }

    // Add average markers if available
    if (perfData.avgMarkers !== undefined) {
      summary += `| **Avg Markers Loaded** | ${perfData.avgMarkers} |\n`;
    }
    summary += '\n';

    // Individual run times
    if (perfData.runTimes && perfData.runTimes.length > 0) {
      summary += '<details>\n';
      summary += '<summary>📈 Individual Run Times</summary>\n\n';

      // Check if marker data is available
      const hasMarkerData = perfData.runTimes[0] && perfData.runTimes[0].markers !== undefined;

      if (hasMarkerData) {
        summary += '| Run | Time (ms) | Markers |\n';
        summary += '|-----|-----------|--------|\n';
        perfData.runTimes.forEach(run => {
          summary += `| Run ${run.run} | ${run.time}ms | ${run.markers} |\n`;
        });
      } else {
        summary += '| Run | Time (ms) |\n';
        summary += '|-----|----------|\n';
        perfData.runTimes.forEach(run => {
          summary += `| Run ${run.run} | ${run.time}ms |\n`;
        });
      }
      summary += '\n</details>\n';
    }
  }

  return summary;
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: node generate-perf-summary.js <perf-json-path> [--format=github|pr-comment]');
    process.exit(1);
  }

  const perfPath = args[0];
  const formatArg = args.find(arg => arg.startsWith('--format='));
  const format = formatArg ? formatArg.split('=')[1] : 'github';

  if (!['github', 'pr-comment'].includes(format)) {
    console.error('Invalid format. Use --format=github or --format=pr-comment');
    process.exit(1);
  }

  const summary = generatePerfSummary(perfPath, format);
  console.log(summary);
}

module.exports = { generatePerfSummary };
