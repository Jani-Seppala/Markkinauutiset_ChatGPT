import React, { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';
import { useLocation } from 'react-router-dom';
import axios from './AxiosSetup';
import NewsItem from './NewsItem';
import FlashMessage from './FlashMessage';

// const socket = io(axios.defaults.baseURL, { transports: ['websocket'] });

const socket = io(axios.defaults.baseURL, {
    transports: ['websocket'],
    reconnectionAttempts: 5,
    reconnectionDelayMax: 10000
});


console.log("axios.defaults.baseURL:", axios.defaults.baseURL);
// const socket = io('http://localhost:5000', { transports: ['websocket'] });
// const socket = io('http://localhost:5000'); // Connect to the server where your Flask app is running
// const socket = io(axios.defaults.baseURL);
// const socket = io.connect('http://localhost:5000', {transports: ['websocket', 'polling']});

// socket.on('connect', () => {
//     console.log('Connected to server');
// });

socket.on('update_news', function(data) {
    console.log('Received news update:', data);
});


socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});




function NewsAndAnalysis({ stockIds, token, isSoundOn }) {
    const [newsWithAnalysis, setNewsWithAnalysis] = useState([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loading, setLoading] = useState(false);
    const location = useLocation();

    const playNotificationSound = useCallback(() => {
        console.log("isSoundOn:", isSoundOn);
        if (isSoundOn) {
            const sound = new Audio('/notification.mp3');
            sound.play().catch(error => console.log("Failed to play sound:", error));
        }
    }, [isSoundOn]); // Dependency array includes isSoundOn
    

    const fetchNews = useCallback((currentPage, reset = false) => {
        setLoading(true);
        // const baseUrl = 'http://localhost:5000/api/news-with-analysis';
        // const baseUrl = `${process.env.REACT_APP_API_BASE_URL}/api/news-with-analysis`;
        const baseUrl = `/api/news-with-analysis`; // Use relative URL
        const params = new URLSearchParams({
            page: currentPage
        });

        if (stockIds) {
            params.append('stock_ids', stockIds.join(','));
        }

        axios.get(`${baseUrl}?${params.toString()}`, {
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (reset) {
                setNewsWithAnalysis(response.data.items);
            } else {
                setNewsWithAnalysis(prev => [...prev, ...response.data.items]);
            }

            setHasMore(response.data.has_more);
            setPage(currentPage + 1); // Increment page if there's more to load
            setLoading(false);
        }).catch(error => {
            console.error("Failed to fetch news", error);
            setLoading(false);
        });
    }, [token, stockIds]);

    useEffect(() => {
        console.log("Setting up socket event listeners");
        // Only set up the listener if on the front page
        if (location.pathname === '/') { // Assuming '/' is your front page route
            console.log("if lauseessa / jälkeen");
            socket.on('update_news', data => {
                console.log(data.message);
                playNotificationSound();
                fetchNews(1, true);
            });
        }
    
        return () => {
            console.log("Cleaning up socket event listeners");
            socket.off('update_news');
        };
    }, [fetchNews, playNotificationSound, location.pathname]); // Add location.pathname to the dependency array
          
    useEffect(() => {
        fetchNews(1, true); // Fetch the first page and reset the news list
    }, [stockIds, token, fetchNews]);
    

    // console.log('News item IDs:', newsWithAnalysis.map(({ news }) => news._id));

    return (
        <div className="container">
            <h1 className="text-center mb-4">News and Analysis</h1>
            {location.state?.message && (
                <FlashMessage message={location.state.message} type={location.state.type} />
            )}
            {loading ? (
                <p>Loading...</p>
            ) : (
                newsWithAnalysis.length === 0 ? (
                    <p>No news for this company.</p>
                ) : (
                    newsWithAnalysis.map(({ news, analysis }, index) => {
                        // Ensure the key is a string. Access the $oid property if _id is an object.
                        const keyId = news._id && news._id.$oid ? news._id.$oid : index.toString();
                        // console.log(`Key for NewsItem ${index}: ${keyId}`); // Check what key is used.
                        return <NewsItem key={keyId} news={news} analysis={analysis} />;
                    })
                )
            )}
            {!loading && hasMore && (
                <button onClick={() => fetchNews(page)} className="btn btn-primary">
                    Show More
                </button>
            )}
        </div>
    );
}

export default NewsAndAnalysis;