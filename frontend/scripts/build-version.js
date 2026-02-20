const fs = require('fs');
const path = require('path');

// Read current package.json
const packageJsonPath = path.join(__dirname, '../package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Parse current version
const currentVersion = packageJson.version;
const [major, minor, patch] = currentVersion.split('.').map(Number);

// Increment minor version
const newMinorVersion = minor + 1;
const newVersion = `${major}.${newMinorVersion}.${patch}`;

// Update package.json
packageJson.version = newVersion;
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));

// Generate build date
const buildDate = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
});

// Create version.ts file with build-time values
const versionTsContent = `export const APP_VERSION = "${newVersion}";
export const BUILD_DATE = "${buildDate}";
`;

const versionTsPath = path.join(__dirname, '../src/version.ts');
fs.writeFileSync(versionTsPath, versionTsContent);

console.log(`✅ Version updated to ${newVersion}`);
console.log(`✅ Build date set to ${buildDate}`);
console.log(`✅ Version file generated at ${versionTsPath}`);
