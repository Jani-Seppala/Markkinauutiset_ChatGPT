// import React, { useState } from 'react';
// import { Link } from 'react-router-dom';
// import './NewsItem.css';
// import { useUser } from './UserContext';

// const marketToFlag = {
//   "Helsinki": "/flags/fi.png",
//   "Copenhagen": "/flags/dk.png",
//   "Stockholm": "/flags/se.png",
//   "Oslo": "/flags/no.png",
//   "Iceland": "/flags/is.png",
//   "Sweden": "/flags/se.png",
//   "Finland": "/flags/fi.png",
//   "Denmark": "/flags/dk.png"
// };

// function getFlagForMarket(market) {
//   const countryKey = Object.keys(marketToFlag).find(key => market.includes(key));
//   return marketToFlag[countryKey];
// }

// function NewsItem({ news, analysis, selectedLanguage }) {
//   const { darkMode } = useUser(); // Access darkMode state
//   const [isExpanded, setIsExpanded] = useState(false);
//   const flagSrc = getFlagForMarket(news.market);

//   // Determine the classes to apply based on darkMode
//   const newsItemClass = darkMode ? "news-item my-3 p-3 bg-dark text-white border rounded" : "news-item my-3 p-3 bg-light text-dark border rounded";

//   // This function toggles the expanded state
//   const toggleExpand = () => {
//     setIsExpanded(!isExpanded);
//   };

//   // Prevents the link click from propagating to the parent div
//   const handleLinkClick = (e) => {
//     e.stopPropagation();
//   };

//     // Function to format analysis content with line breaks
//     const formatAnalysisContent = (content) => {
//       return content.split('\n').map((text, index) => (
//         <span key={index}>
//           {text}
//           <br />
//         </span>
//       ));
//     };

//   // Determine which analysis content to display based on selectedLanguage
//   let analysisContent = '';

//   if (analysis) {
//     if (selectedLanguage === 'english' && analysis.analysis_content) {
//       analysisContent = analysis.analysis_content;
//     } else if (selectedLanguage === 'finnish' && analysis.analysis_content_fi) {
//       analysisContent = analysis.analysis_content_fi;
//     } else {
//       // Handle case where analysis in the selected language is not available
//       analysisContent = 'Analyysia ei ole saatavilla Suomen kielellä'; // Or you can set a fallback message
//     }
//   }


//   return (
//     <div className={newsItemClass} onClick={toggleExpand}>
//       <div className="news-header mb-2">
//         {flagSrc && <img src={flagSrc} alt="Country flag" style={{ width: "20px", marginRight: "5px", verticalAlign: "middle" }} />}
//         {/* Wrap the company name in a span and Link component */}
//         <span onClick={handleLinkClick}>
//             <Link to={`/stocks/${news.stock_id.$oid || news.stock_id}`} className="company-name-link">
//             {news.company}
//             </Link>
//         </span>
//         <span className="release-time">{news.releaseTime}</span>
//       </div>
//       <span onClick={handleLinkClick}>
//         <a href={news.messageUrl} target="_blank" rel="noopener noreferrer" className="headline-link">
//           <h4 className="headline">{news.headline}</h4>
//         </a>
//       </span>
//         {analysisContent && (
//           <div
//             className={`analysis-content mt-3 ${
//               isExpanded ? 'expanded' : 'collapsed'
//             }`}
//           >
//             <h5>Analysis</h5>
//             {isExpanded ? (
//               formatAnalysisContent(analysisContent)
//             ) : (
//               `${analysisContent.substring(0, 100)}...`
//             )}
//             {!isExpanded && <div className="click-to-enlarge">Click to enlarge</div>}
//           </div>
//       )}
//     </div>
//   );
// }

// export default NewsItem;

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './NewsItem.css';
import { useUser } from './UserContext';
import DOMPurify from 'dompurify';

const marketToFlag = {
  "Helsinki": "/flags/fi.png",
  "Copenhagen": "/flags/dk.png",
  "Stockholm": "/flags/se.png",
  "Oslo": "/flags/no.png",
  "Iceland": "/flags/is.png",
  "Sweden": "/flags/se.png",
  "Finland": "/flags/fi.png",
  "Denmark": "/flags/dk.png"
};

function getFlagForMarket(market) {
  const countryKey = Object.keys(marketToFlag).find(key => market.includes(key));
  return marketToFlag[countryKey];
}

function NewsItem({ news, analysis, selectedLanguage }) {
  const { darkMode } = useUser(); // Access darkMode state
  const [isExpanded, setIsExpanded] = useState(false);
  const flagSrc = getFlagForMarket(news.market);

  // Determine the classes to apply based on darkMode
  const newsItemClass = darkMode
    ? "news-item my-3 p-3 bg-dark text-white border rounded"
    : "news-item my-3 p-3 bg-light text-dark border rounded";

  // Toggle the expanded state
  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  // Prevent the link click from propagating to the parent div
  const handleLinkClick = (e) => {
    e.stopPropagation();
  };

  // Determine which analysis content to display based on selectedLanguage
  let analysisContent = '';

  if (analysis) {
    if (selectedLanguage === 'english' && analysis.analysis_content) {
      analysisContent = analysis.analysis_content;
    } else if (selectedLanguage === 'finnish' && analysis.analysis_content_fi) {
      analysisContent = analysis.analysis_content_fi;
    } else {
      // Handle case where analysis in the selected language is not available
      analysisContent = 'Analysis not available in the selected language.';
    }
  }


  
  // Sanitize the analysisContent for safe HTML rendering
  const sanitizedAnalysisContent = DOMPurify.sanitize(analysisContent);

  // Sanitize and strip all HTML tags for the collapsed preview
  const strippedAnalysisContent = DOMPurify.sanitize(analysisContent, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
  

  // Function to truncate the stripped content
  const truncateContent = (content, maxLength) => {
    if (content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className={newsItemClass} onClick={toggleExpand}>
      <div className="news-header mb-2">
        {flagSrc && (
          <img
            src={flagSrc}
            alt="Country flag"
            style={{ width: "20px", marginRight: "5px", verticalAlign: "middle" }}
          />
        )}
        {/* Wrap the company name in a span and Link component */}
        <span onClick={handleLinkClick}>
          <Link to={`/stocks/${news.stock_id.$oid || news.stock_id}`} className="company-name-link">
            {news.company}
          </Link>
        </span>
        <span className="release-time">{news.releaseTime}</span>
      </div>
      <span onClick={handleLinkClick}>
        <a href={news.messageUrl} target="_blank" rel="noopener noreferrer" className="headline-link">
          <h4 className="headline">{news.headline}</h4>
        </a>
      </span>
      {analysisContent && (
        <div
          className={`analysis-content mt-3 ${
            isExpanded ? 'expanded' : 'collapsed'
          }`}
        >
          <h5>Analysis</h5>
          {isExpanded ? (
            // Render the sanitized HTML content safely
            <div dangerouslySetInnerHTML={{ __html: sanitizedAnalysisContent }} />
          ) : (
            // Render the truncated plain text preview
            <div>
              {truncateContent(strippedAnalysisContent, 200)}
              {!isExpanded && <div className="click-to-enlarge">Click to enlarge</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NewsItem;
