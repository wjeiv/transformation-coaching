FROM node:20-alpine

WORKDIR /app

COPY package.json ./
COPY scripts/ ./scripts/
RUN npm install

COPY . .

# Run build version script to set build date and increment version
RUN node scripts/build-version.js

EXPOSE 3000

CMD ["npm", "start"]
