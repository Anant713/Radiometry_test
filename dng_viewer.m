img = rawread('C:\Users\Anant\OneDrive\Desktop\vbn_data\vbn_data\blob_size_data\range0_exp200_1.dng');
%imshow(img,[]);
%impixelinfo;
img8 = uint8(img / 256);
imshow(img8,[]);
impixelinfo;
%imtool(img8);