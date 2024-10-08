import React, { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';
import { useLocation } from 'react-router-dom';
import axios from './AxiosSetup';
import NewsItem from './NewsItem';
import FlashMessage from './FlashMessage';
import InfiniteScroll from 'react-infinite-scroll-component';

// const socket = io(axios.defaults.baseURL, { transports: ['websocket'] });

const socket = io(axios.defaults.baseURL, {
    transports: ['websocket'],
    reconnectionAttempts: 5,
    reconnectionDelayMax: 10000
});

// console.log("axios.defaults.baseURL:", axios.defaults.baseURL);

socket.on('update_news', function(data) {
    console.log('Received news update:', data);
});


socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});

socket.on('error', (error) => {
    console.error('Error:', error);
});

function NewsAndAnalysis({ stockIds, token, isSoundOn }) {
    const [newsWithAnalysis, setNewsWithAnalysis] = useState([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    // const [loading, setLoading] = useState(false);
    const location = useLocation();
    const [selectedMarkets, setSelectedMarkets] = useState(['finnish', 'swedish']);
    const [selectedLanguage, setSelectedLanguage] = useState('english'); // Default to English


    const playNotificationSound = useCallback(() => {
        console.log("isSoundOn:", isSoundOn);
        if (isSoundOn) {
            const sound = new Audio('/notification.mp3');
            sound.play().catch(error => console.log("Failed to play sound:", error));
        }
    }, [isSoundOn]); // Dependency array includes isSoundOn
    
    const handleMarketChange = (market) => {
        setSelectedMarkets(prev => {
            if (prev.includes(market)) {
                return prev.filter(m => m !== market);
            } else {
                return [...prev, market];
            }
        });
    };

    const fetchNews = useCallback((currentPage, reset = false) => {
        // setLoading(true);
        const baseUrl = `/api/news-with-analysis`; // Use relative URL
        const params = new URLSearchParams({
            page: currentPage
        });

        if (stockIds) {
            params.append('stock_ids', stockIds.join(','));
        }

        if (selectedMarkets.length > 0) {
            selectedMarkets.forEach(market => params.append('market', market));
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
            // setLoading(false);
        }).catch(error => {
            console.error("Failed to fetch news", error);
            // setLoading(false);
        });
    }, [token, stockIds, selectedMarkets]);

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
    }, [selectedMarkets, stockIds, token, fetchNews]);
    

    // console.log('News item IDs:', newsWithAnalysis.map(({ news }) => news._id));

    return (
        <div className="container">
        <h1 className="text-center mb-4">News and Analysis</h1>
        {location.state?.message && (
            <FlashMessage message={location.state.message} type={location.state.type} />
        )}
        <div>
            <label>
            <input
                type="checkbox"
                value="finnish"
                onChange={() => handleMarketChange('finnish')}
                checked={selectedMarkets.includes('finnish')}
            />
            Finnish Markets
            </label>
            <label>
            <input
                type="checkbox"
                value="swedish"
                onChange={() => handleMarketChange('swedish')}
                checked={selectedMarkets.includes('swedish')}
            />
            Swedish Markets
            </label>
        </div>
        <div>
            <label>
            <input
                type="radio"
                value="english"
                onChange={() => setSelectedLanguage('english')}
                checked={selectedLanguage === 'english'}
            />
            English
            </label>
            <label>
            <input
                type="radio"
                value="finnish"
                onChange={() => setSelectedLanguage('finnish')}
                checked={selectedLanguage === 'finnish'}
            />
            Finnish
            </label>
        </div>

        {newsWithAnalysis.length === 0 ? (
            <p>No news for this company.</p>
        ) : (
            <InfiniteScroll
            dataLength={newsWithAnalysis.length}
            next={() => fetchNews(page)}
            hasMore={hasMore}
            loader={<h4>Loading...</h4>}
            endMessage={
                <p style={{ textAlign: 'center' }}>
                <b>No more news to display</b>
                </p>
            }
            >
            {newsWithAnalysis.map(({ news, analysis }, index) => {
                const keyId = news._id && news._id.$oid ? news._id.$oid : index.toString();
                return (
                <NewsItem
                    key={keyId}
                    news={news}
                    analysis={analysis}
                    selectedLanguage={selectedLanguage}
                />
                );
            })}
            </InfiniteScroll>
        )}
        </div>
    );
}

export default NewsAndAnalysis;