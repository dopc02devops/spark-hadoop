# Step 1: Set the base image
FROM node:18

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy package.json and package-lock.json first to take advantage of Docker cache
COPY package.json package-lock.json ./

# Step 4: Install dependencies using npm ci (faster & consistent)
RUN npm ci --omit=dev

# Step 5: Copy the rest of the application files into the container
COPY . . 

# Step 7: Expose port 3000 for the React app
EXPOSE 3000

# Step 8: Start the React application
CMD ["npm", "start"]
