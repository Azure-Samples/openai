import React, { useState } from "react";
import "./ImageGallery.css";

interface ImageGalleryProps {
  images: string[];
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({ images }) => {
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  const handleImageClick = (imageUrl: string) => {
    setExpandedImage(imageUrl);
  };

  const handleCloseExpanded = () => {
    setExpandedImage(null);
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleCloseExpanded();
    }
  };

  return (
    <>
      <div className="image-gallery">
        {images.map((imageUrl, index) => (
          <div key={index} className="image-thumbnail-container">
            <img
              src={imageUrl}
              alt={`Generated chart ${index + 1}`}
              className="image-thumbnail"
              onClick={() => handleImageClick(imageUrl)}
              loading="lazy"
            />
          </div>
        ))}
      </div>

      {expandedImage && (
        <div className="image-overlay" onClick={handleOverlayClick}>
          <div className="image-expanded-container">
            <button
              className="image-close-button"
              onClick={handleCloseExpanded}
              aria-label="Close expanded image"
            >
              ×
            </button>
            <img
              src={expandedImage}
              alt="Expanded chart"
              className="image-expanded"
            />
          </div>
        </div>
      )}
    </>
  );
};
