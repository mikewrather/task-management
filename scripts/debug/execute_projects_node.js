#!/usr/bin/env node

const { exec } = require('child_process');
const path = require('path');

// Change to project directory
process.chdir('/home/mike/development/task-management');

const prompt = `Use the mcp__agent-db__execute_cypher tool with these exact parameters:
{
  "query": "\\n        MATCH (p:PROJECT)-[:BELONGS_TO]->(a:AREA)\\n        RETURN p.notion_id as project_id, p.name as name, \\n               a.notion_id as area_id, a.name as area_name\\n        ",
  "parameters": {}
}

Return ONLY the raw JSON result from the tool, with no additional text or formatting.`;

const cmd = `claude -p "${prompt}" --dangerously-skip-permissions --output-format json`;

exec(cmd, { timeout: 120000 }, (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    if (stderr) {
        console.error(`Stderr: ${stderr}`);
        return;
    }
    
    try {
        const response = JSON.parse(stdout);
        if (response.content) {
            try {
                const data = JSON.parse(response.content);
                console.log(JSON.stringify(data));
            } catch {
                console.log(response.content);
            }
        } else {
            console.log(JSON.stringify(response));
        }
    } catch (e) {
        console.log(stdout);
    }
});