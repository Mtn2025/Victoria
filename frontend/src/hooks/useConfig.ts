import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
// Assuming configSlice exists and exports actions
// import { updateConfig } from '../store/slices/configSlice'; 

export const useConfig = () => {
    // const dispatch = useDispatch();
    const config = useSelector((state: RootState) => state.config);

    return { config };
};
