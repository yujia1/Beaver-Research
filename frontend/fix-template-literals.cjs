#!/usr/bin/env node

/**
 * Script to fix template literal syntax - replace single quotes with backticks
 * Usage: node fix-template-literals.cjs
 */

const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

function getAllFiles(dirPath, arrayOfFiles = []) {
    const files = fs.readdirSync(dirPath);

    files.forEach(file => {
        const filePath = path.join(dirPath, file);
        if (fs.statSync(filePath).isDirectory()) {
            arrayOfFiles = getAllFiles(filePath, arrayOfFiles);
        } else if (file.endsWith('.vue') || file.endsWith('.js')) {
            arrayOfFiles.push(filePath);
        }
    });

    return arrayOfFiles;
}

function fixInFile(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Check if file contains the broken pattern
    if (content.includes('\'${API_BASE_URL}')) {
        console.log(`Fixing: ${filePath}`);

        // Replace '${API_BASE_URL}...' with `${API_BASE_URL}...`
        const newContent = content.replace(/'(\$\{API_BASE_URL\}[^']*)'/g, '`$1`');

        fs.writeFileSync(filePath, newContent, 'utf8');
        console.log(`  ✓ Fixed template literals`);
        modified = true;
    }

    return modified;
}

// Main execution
console.log('Fixing template literal syntax...\n');

const files = getAllFiles(srcDir);
let modifiedCount = 0;

files.forEach(file => {
    if (fixInFile(file)) {
        modifiedCount++;
    }
});

console.log(`\n✅ Complete! Fixed ${modifiedCount} files.`);
