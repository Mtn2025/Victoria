import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store/store';
import { loginStart, loginSuccess, loginFailure, logout } from '../store/slices/authSlice';
import { api } from '../services/api';

export const useAuth = () => {
    const dispatch = useDispatch();
    const { user, isAuthenticated, status } = useSelector((state: RootState) => state.auth);

    const login = async (credentials: any) => {
        dispatch(loginStart());
        try {
            const response = await api.post<{ user: any, token: string }>('/auth/login', credentials);
            dispatch(loginSuccess(response));
        } catch (error) {
            dispatch(loginFailure());
            throw error;
        }
    };

    const logoutUser = () => {
        dispatch(logout());
    };

    return { user, isAuthenticated, status, login, logout: logoutUser };
};
