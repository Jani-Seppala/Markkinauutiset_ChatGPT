import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
// import NewsItem from './NewsItem';
import NewsAndAnalysis from './NewsAndAnalysis';

function StockPage() {
  const { stockId } = useParams();
  const [stockData, setStockData] = useState(null);
  // const [newsData, setNewsData] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchStockData = async () => {
      try {
        // const response = await axios.get(`http://localhost:5000/api/stocks/${stockId}`);
        const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/stocks/${stockId}`);
        // console.log('Stock Response:', response); // Debug print
        setStockData(response.data);
  
        if (token) {
          // const favoritesResponse = await axios.get('http://localhost:5000/api/favorites', {
          const favoritesResponse = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/favorites`, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          // console.log('Favorites Response:', favoritesResponse.data);
          setFavorites(favoritesResponse.data.map(stock => stock._id));
        }
        setLoading(false);
      } catch (err) {
        // console.error('Error:', err); // Debug print
        setError('Failed to fetch data');
        setLoading(false);
      }
    };
  
    fetchStockData();
  }, [stockId, token]);


  const handleAddToFavorites = (stockToAdd) => {
    const userId = localStorage.getItem('userId');
    if (!favorites.includes(stockToAdd._id)) {
      
      // axios.post(`http://localhost:5000/api/users/${userId}/add_favorite/${stockToAdd._id}`, {}, {
      axios.post(`${process.env.REACT_APP_API_BASE_URL}/api/users/${userId}/add_favorite/${stockToAdd._id}`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .then(() => {
        const newFavorites = [...favorites, stockToAdd._id];
        setFavorites(newFavorites);
        // console.log('Favorites after adding:', newFavorites);
      })
      .catch(error => console.error("Failed to add stock to favorites", error));
    }
  };

  const handleRemoveFromFavorites = () => {
    const updatedFavorites = favorites.filter(favoriteId => favoriteId !== stockId);
    setFavorites(updatedFavorites);
    // console.log('Favorites after removing:', updatedFavorites);
    // axios.post('http://localhost:5000/api/favorites', { favorites: updatedFavorites }, {
    axios.post(`${process.env.REACT_APP_API_BASE_URL}/api/favorites`, { favorites: updatedFavorites }, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }).catch(error => console.error("Failed to update favorites", error));
  
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  // console.log('Favorites:', favorites);
  // console.log('Stock ID:', stockId);
  const isFavorite = favorites.includes(stockId);
  // console.log('Is Favorite:', isFavorite);


return (
  <div>
    <h2>Stock Details</h2>
    {stockData ? (
      <div className="d-flex justify-content-between align-items-center">
        <h3>{stockData.name} ({stockData.symbol})</h3>
        {token && (
          <button className={`btn ${isFavorite ? 'btn-danger' : 'btn-primary'}`} onClick={() => isFavorite ? handleRemoveFromFavorites() : handleAddToFavorites(stockData)}>
            {isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
          </button>
        )}
      </div>
    ) : (
      <p>Stock information not available.</p>
    )}
    <NewsAndAnalysis stockIds={[stockId]} token={token} />
  </div>
);
}

export default StockPage;