import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { DataProvider } from './src/context/DataContext';
import { AuthProvider } from './src/context/AuthContext';
import { AppNavigator } from './src/navigation/AppNavigator';

export default function App() {
  return (
    <DataProvider>
      <AuthProvider>
        <StatusBar style="light" />
        <AppNavigator />
      </AuthProvider>
    </DataProvider>
  );
}
