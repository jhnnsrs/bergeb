foo=('0.6' '0.7' )
templates = ()

for i in "${!foo[@]}"; do 
  if [ "$i" -eq "0" ]; then
    printf 'First'
    printf "%s\t%s\n" "$i" "${foo[$i]}"
  else
    printf 'Second'
    printf "%s\t%s\n" "$i" "${foo[$i]}"
  fi
done