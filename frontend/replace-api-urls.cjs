#!/usr/bin/env node

/**
 * Script to replace hardcoded localhost:8000 URLs with environment variable
 * Usage: node replace-api-urls.js
 */

const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');
const API_CONFIG_IMPORT = "import API_BASE_URL from '@/config/api.js'";

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

function replaceInFile(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Check if file contains localhost:8000
    if (content.includes('http://localhost:8000')) {
        console.log(`Processing: ${filePath}`);

        // Replace all occurrences
        const newContent = content.replace(/http:\/\/localhost:8000/g, '${API_BASE_URL}');

        // Add import if it's a .vue file and doesn't have it
        if (filePath.endsWith('.vue') && !content.includes(API_CONFIG_IMPORT)) {
            // Find the script setup tag
            if (newContent.includes('<script setup>')) {
                const updatedContent = newContent.replace(
                    '<script setup>',
                    `<script setup>\n${API_CONFIG_IMPORT}\n`
                );
                fs.writeFileSync(filePath, updatedContent, 'utf8');
                console.log(`  ✓ Updated and added import`);
                modified = true;
            } else {
                fs.writeFileSync(filePath, newContent, 'utf8');
                console.log(`  ✓ Updated (manual import needed)`);
                modified = true;
            }
        } else {
            fs.writeFileSync(filePath, newContent, 'utf8');
            console.log(`  ✓ Updated`);
            modified = true;
        }
    }

    return modified;
}

// Main execution
console.log('Starting API URL replacement...\n');

const files = getAllFiles(srcDir);
let modifiedCount = 0;

files.forEach(file => {
    if (replaceInFile(file)) {
        modifiedCount++;
    }
});

console.log(`\n✅ Complete! Modified ${modifiedCount} files.`);
console.log('\nNext steps:');
console.log('1. Review the changes with: git diff');
console.log('2. Test locally: npm run dev');
console.log('3. Commit and push to Railway');
