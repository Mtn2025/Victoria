import React from 'react';

export const Footer: React.FC = () => {
    return (
        <footer className="bg-gray-100 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-4 px-6 text-center text-sm text-gray-600 dark:text-gray-400">
            <p>&copy; {new Date().getFullYear()} Asistente Andrea. All rights reserved.</p>
        </footer>
    );
};
