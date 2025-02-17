import React, { useState, useEffect } from 'react';

const App = () => {
  const [financialData, setFinancialData] = useState([]);
  const [cryptoData, setCryptoData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data once when the component mounts
    const fetchData = async () => {
      try {
        // Fetch financial data
        const financialResponse = await fetch('http://localhost:6500/api/financial');
        const financialData = await financialResponse.json();
        setFinancialData(financialData);

        // Fetch crypto data
        const cryptoResponse = await fetch('http://localhost:6500/api/crypto');
        const cryptoData = await cryptoResponse.json();
        setCryptoData(cryptoData);

        // Set loading to false after data is fetched
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false); // In case of error, set loading to false
      }
    };

    fetchData();

    // Set up an interval to fetch data every 3 seconds
    const interval = setInterval(() => {
      fetchData();
    }, 3000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []); // Empty dependency array makes this run only once when the component mounts

  if (loading) {
    return <div>Loading...</div>; // Show loading state until data is fetched
  }

  return (
    <div>
      <h1>Financial Data</h1>
      <ul>
        {financialData.map((data, index) => (
          <li key={index}>{data.symbol}: {data.price}</li>
        ))}
      </ul>
      
      <h1>Crypto Data</h1>
      <ul>
        {cryptoData.map((data, index) => (
          <li key={index}>{data.symbol}: {data.price}</li>
        ))}
      </ul>
    </div>
  );
};

export default App;
