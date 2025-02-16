# Step 1: Set the base image
FROM node:18

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy package.json and package-lock.json first to take advantage of Docker cache
COPY package.json package-lock.json /app/

# Step 4: Install dependencies (including "web-vitals" if it's missing)
RUN npm install

# Step 5: Copy the rest of the application files into the container
COPY . /app

# Set OpenSSL legacy provider
ENV NODE_OPTIONS="--openssl-legacy-provider"

# Step 6: Expose port 3000 for the React app
EXPOSE 3000

# Step 7: Start the React application
CMD ["npm", "start"]
