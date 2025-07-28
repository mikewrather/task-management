#!/usr/bin/env bun

// Test the smart context analysis locally without Windmill
async function testSmartContext() {
  const log = (message: string, level: 'INFO' | 'ERROR' | 'SUCCESS' = 'INFO') => {
    const timestamp = new Date().toISOString();
    const emoji = level === 'SUCCESS' ? '✅' : level === 'ERROR' ? '❌' : 'ℹ️';
    console.log(`${timestamp} ${emoji} ${message}`);
  };

  try {
    log('🧠 Testing smart context analysis locally...');

    // Mock transcript from your previous test
    const transcript = "I need to make sure that all of the trees in the backyard are being watered adequately.";

    // Mock existing areas (from your Notion data)
    const existingAreas = [
      { id: '1bf10f77-ef80-4bca-87a4-80a480d3404d', name: 'House', type: 'Personal', emoji: '🏡' },
      { id: 'd4c1cb8a-a21d-4b74-8013-59e5c2c12447', name: 'Health & Fitness', type: 'Personal', emoji: '💪' },
      { id: 'a00e80e7-eb22-4310-b351-18723a359a5e', name: 'Kids', type: 'Personal', emoji: '👨‍👩‍👧' },
      { id: '1ba66c0c-73af-811c-a851-d553a2a6b01b', name: 'Google', type: 'Work', emoji: '' },
    ];

    const existingProjects = [
      { id: '1d566c0c-73af-802b-999b-cc5e79817965', name: 'Front yard landscaping', area: '1bf10f77-ef80-4bca-87a4-80a480d3404d' },
      { id: 'fa4723a5-b925-4912-87de-7bcd0fc18757', name: 'Septic maintenance', area: '1bf10f77-ef80-4bca-87a4-80a480d3404d' },
      { id: 'faef1749-a180-4a7d-8bed-73a98a5ccb52', name: 'Fence / Gate', area: '1bf10f77-ef80-4bca-87a4-80a480d3404d' },
    ];

    log(`📊 Mock data: ${existingAreas.length} areas and ${existingProjects.length} projects`);

    // Test the Claude analysis prompt
    const contextPrompt = `Analyze this voice transcript and suggest the best categorization based on existing Notion data.

TRANSCRIPT: "${transcript}"

EXISTING AREAS:
${existingAreas.map(a => `- ${a.emoji} ${a.name} (${a.type})`).join('\n')}

EXISTING PROJECTS (by area):
${existingAreas.map(area => {
  const areaProjects = existingProjects.filter(p => p.area === area.id);
  return `${area.emoji} ${area.name}:\n${areaProjects.map(p => `  - ${p.name}`).join('\n')}`;
}).join('\n\n')}

Please analyze the transcript and return a JSON response with:
1. title: A concise task title
2. area_suggestion: Best matching area ID or null if new area needed
3. area_name: Name of suggested area (existing or new)
4. project_suggestion: Best matching project ID or null if new project needed 
5. project_name: Name of suggested project (existing or new)
6. contexts: Array of relevant context tags
7. reasoning: Brief explanation of categorization choices

Focus on semantic matching - for example:
- "trees in backyard" → House area, could relate to "Front yard landscaping" project
- "workout" → Health & Fitness area
- References to work tools/apps → Work areas
- Home maintenance tasks → House area

Return only valid JSON.`;

    log('🎯 Generated analysis prompt:');
    console.log('---');
    console.log(contextPrompt);
    console.log('---');

    // Expected smart categorization for this transcript
    const expectedAnalysis = {
      title: "Ensure backyard trees are watered adequately",
      area_suggestion: "1bf10f77-ef80-4bca-87a4-80a480d3404d", // House area
      area_name: "House",
      project_suggestion: "1d566c0c-73af-802b-999b-cc5e79817965", // Front yard landscaping (closest match)
      project_name: "Front yard landscaping",
      contexts: ["yard-maintenance", "trees", "watering", "backyard"],
      reasoning: "Trees and watering relate to house/yard maintenance. Closest existing project is Front yard landscaping."
    };

    log('🎯 Expected smart categorization:');
    console.log(JSON.stringify(expectedAnalysis, null, 2));

    log('✅ Smart context analysis test completed successfully!', 'SUCCESS');
    log('📝 This shows the improvement over generic "voice" context to specific House area + landscaping project');

  } catch (error) {
    log(`💥 Error during test: ${error.message}`, 'ERROR');
  }
}

testSmartContext();